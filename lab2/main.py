import sys
from typing import *

import numpy as np
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidget, QTableWidgetItem, QPushButton, \
    QGroupBox

from lab2.horse import Horse
from lab2.queue import distributions
from lab2.queue.generator import Generator
from lab2.queue.modeller import Modeller
from lab2.queue.processor import Processor

ROUND_TO = 5


class mywindow(QMainWindow):
    def __init__(self):
        super(mywindow, self).__init__()
        uic.loadUi('mainwindow.ui', self)
        self.show()

        self.pushButton_model.clicked.connect(self.modeling_button_clicked)
        self.check_button: QPushButton
        self.check_button.clicked.connect(self.check_button_clicked)
        self.check_button.setDisabled(True)
        self.groupBox_4: QGroupBox
        self.groupBox_4.hide()

    def old(self):
        try:
            generator_intensity = self.input_intens_generator.value()
            processor_intensity = self.input_intens_processor.value()
            processor_variance = self.input_disp_processor.value()

            generator_intensity = self.horse.natural_factor_from_normalized(
                generator_intensity, self.horse.gen_int_min, self.horse.gen_int_max)
            processor_intensity = self.horse.natural_factor_from_normalized(
                processor_intensity, self.horse.proc_int_min, self.horse.proc_int_max)
            processor_variance = self.horse.natural_factor_from_normalized(
                processor_variance, self.horse.proc_var_min, self.horse.proc_var_max)

            lambda_, mu, sigma = generator_intensity, 1 / processor_intensity, processor_variance
            generators = [Generator(distributions.ExponentialDistribution(lambda_))]
            processors = [Processor(distributions.NormalDistribution(mu, sigma))]
            modeller = Modeller(generators, processors)

            result = modeller.event_modelling(self.horse.requests_amount)

            p_theor = generator_intensity / processor_intensity
            self.res_theor_zagr.setText(str(round(p_theor, ROUND_TO)))

            p_fact = result['p_fact']
            self.res_fact_zagr.setText(str(round(p_fact, ROUND_TO)))

            self.res_exp_mean_time_in_queue.setText(str(round(result['mean_time_in_queue'], ROUND_TO)))

            if p_theor < 1:
                # https://en.wikipedia.org/wiki/M/D/1_queue
                res_theor_mean_time_in_queue = p_theor / (2 * processor_intensity * (1 - p_theor))
                res_theor_mean_time_in_queue = str(round(res_theor_mean_time_in_queue, ROUND_TO))
            else:
                res_theor_mean_time_in_queue = ''
            self.res_theor_mean_time_in_queue.setText(res_theor_mean_time_in_queue)

        except Exception as e:
            error_msg = QMessageBox()
            error_msg.setText('Ошибка!\n' + repr(e))
            error_msg.show()
            error_msg.exec()

    def check_button_clicked(self):
        self.old()
        generator_intensity = self.input_intens_generator.value()
        processor_intensity = self.input_intens_processor.value()
        processor_variance = self.input_disp_processor.value()

        row = self.horse.check(generator_intensity, processor_intensity, processor_variance)
        row = np.round(row, ROUND_TO)
        self.tableWidget.insertRow(self.tableWidget.rowCount())
        for j, column in enumerate(row):
            self.tableWidget.setItem(self.tableWidget.rowCount() - 1, j, QTableWidgetItem(str(row[j])))

    def create_generators_and_processors(self) -> (List[Generator], List[Processor]):
        generators = []
        processors = []

        # матожидание экспоненциального распределения = 1 / lambda
        # интенсивность = 1 / матожидание экспоненциального распределения
        # lambda = интенсивность
        generator_intensity = self.input_intens_generator.value()
        lambda_ = generator_intensity
        generator = Generator(distributions.ExponentialDistribution(lambda_))

        generators.append(generator)

        processor_intensity = self.input_intens_processor.value()
        processor_range = self.input_disp_processor.value()

        m = 1 / processor_intensity
        sigma = processor_range
        processor = Processor(distributions.NormalDistribution(m, sigma))

        processors.append(processor)

        return generators, processors

    def modeling_button_clicked(self):
        end_param = self.input_t.value()
        gen_int_min = self.gen_int_min.value()
        gen_int_max = self.gen_int_max.value()
        proc_int_min = self.proc_int_min.value()
        proc_int_max = self.proc_int_max.value()
        proc_var_min = self.proc_var_min.value()
        proc_var_max = self.proc_var_max.value()
        if (gen_int_min >= gen_int_max or proc_int_min >= proc_int_max or
                proc_var_min >= proc_var_max or gen_int_max / proc_int_min >= 1):
            error_msg = QMessageBox()
            error_msg.setText('Проверьте параметры')
            error_msg.show()
            error_msg.exec()

        try:
            self.horse = Horse(gen_int_min, gen_int_max, proc_int_min, proc_int_max, proc_var_min, proc_var_max,
                               end_param)
            full_results_table, coefficients = self.horse.run()
            full_results_table = np.round(full_results_table, ROUND_TO)
            self.coefficients = np.round(coefficients, ROUND_TO)

            # columns = ['x0', 'x1', 'x2', 'x3', 'x1x2', 'x1x3', 'x2x3', 'x1x2x3',
            #            'y', 'y_l', 'y_nl', '|y-yl|', '|y-ynl|']

            self.tableWidget: QTableWidget
            self.tableWidget.clearContents()
            self.tableWidget.setRowCount(0)
            for i, row in enumerate(full_results_table):
                self.tableWidget.insertRow(self.tableWidget.rowCount())
                for j, column in enumerate(row):
                    self.tableWidget.setItem(self.tableWidget.rowCount() - 1, j,
                                             QTableWidgetItem(str(full_results_table[i, j])))

            linear_text = f'{self.coefficients[0]}' \
                          f'{self.coefficients[1]:+}*x1{self.coefficients[2]:+}*x2{self.coefficients[3]:+}*x3'
            nonlinear_text = linear_text + \
                             f'{self.coefficients[4]:+}*x1x2' \
                             f'{self.coefficients[5]:+}*x1x3' \
                             f'{self.coefficients[6]:+}*x2x3' \
                             f'{self.coefficients[7]:+}*x1x2x3'
            self.linear.setText(linear_text)
            self.nonlinear.setText(nonlinear_text)

            self.check_button.setDisabled(False)

        except Exception as e:
            error_msg = QMessageBox()
            error_msg.setText('Ошибка!\n' + repr(e))
            error_msg.show()
            error_msg.exec()


if __name__ == "__main__":
    app = QApplication([])
    application = mywindow()
    application.show()

    sys.exit(app.exec())
