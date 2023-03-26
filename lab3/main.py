import sys
from typing import *

import numpy as np
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidget, QTableWidgetItem, QPushButton, \
    QGroupBox, QComboBox

from lab3.horse import Horse, FACTORS_NUMBER
from lab3.queue import distributions
from lab3.queue.generator import Generator
from lab3.queue.modeller import Modeller
from lab3.queue.processor import Processor
from PyQt5 import QtCore

ROUND_TO = 5

# интервал варьирования загрузки системы: 0.05-0.5 ->
# мин инт генератора / макс инт ОА = 0.01
# макс инт генератора / мин инт ОА = 0.5

# интенсивности ОА одинаковые, интенсивности генераторов складываются. тогда
# инт генератора 0.025 - 1 [0.05 - 2]
# инт ОА         4    - 5


QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

class mywindow(QMainWindow):
    def __init__(self):
        super(mywindow, self).__init__()
        uic.loadUi('mainwindow.ui', self)
        self.show()

        self.pushButton_model.clicked.connect(self.run_PFE_experiment)
        self.check_button.clicked.connect(self.check_button_clicked)
        self.check_button.setDisabled(True)
        self.comboBoxMatrix: QComboBox
        self.comboBoxMatrix.currentIndexChanged.connect(self.show_PFE_results)
        self.comboBoxRegression.currentIndexChanged.connect(self.show_PFE_results)

        cur_min_maxes = self.get_current_min_maxes()
        self.horse = Horse(*cur_min_maxes)

    def get_current_min_maxes(self):
        gen_int_min = self.gen_int_min.value()
        gen_int_max = self.gen_int_max.value()
        proc_int_min = self.proc_int_min.value()
        proc_int_max = self.proc_int_max.value()
        proc_var_min = self.proc_var_min.value()
        proc_var_max = self.proc_var_max.value()

        gen_int_min2 = self.gen_int_min_2.value()
        gen_int_max2 = self.gen_int_max_2.value()
        proc_int_min2 = self.proc_int_min_2.value()
        proc_int_max2 = self.proc_int_max_2.value()
        proc_var_min2 = self.proc_var_min_2.value()
        proc_var_max2 = self.proc_var_max_2.value()

        return [gen_int_min, gen_int_max, proc_int_min, proc_int_max, proc_var_min, proc_var_max,
                gen_int_min2, gen_int_max2, proc_int_min2, proc_int_max2, proc_var_min2, proc_var_max2]

    def check_button_clicked(self):
        try:
            generator_intensity = self.input_intens_generator.value()
            processor_intensity = self.input_intens_processor.value()
            processor_variance = self.input_disp_processor.value()
            generator_intensity2 = self.input_intens_generator_2.value()
            processor_intensity2 = self.input_intens_processor_2.value()
            processor_variance2 = self.input_disp_processor_2.value()

            is_natural = self.comboBoxCheck.currentIndex() == 1
            self.horse.check(generator_intensity, processor_intensity, processor_variance,
                             generator_intensity2, processor_intensity2, processor_variance2, is_natural)
            self.show_PFE_results(0)

        except Exception as e:
            self.handle_error(repr(e))

    def show_PFE_results(self, i):
        try:
            if self.comboBoxMatrix.currentIndex() == 0:
                full_results_table = self.horse.norm_full_results_table
            else:
                full_results_table = self.horse.nat_full_results_table

            full_results_table = np.round(full_results_table, ROUND_TO)

            self.tableWidget.clear()
            self.tableWidget.setColumnCount(len(self.horse.PFE_column_names))
            # for i in range(len(self.horse.PFE_column_names)):
            #     self.tableWidget.insertColumn(i + 1)
            self.tableWidget.setHorizontalHeaderLabels(self.horse.PFE_column_names)

            self.tableWidget.setRowCount(0)
            for i, row in enumerate(full_results_table):
                self.tableWidget.insertRow(self.tableWidget.rowCount())
                for j, column in enumerate(row):
                    self.tableWidget.setItem(self.tableWidget.rowCount() - 1, j,
                                             QTableWidgetItem(str(full_results_table[i, j])))

            if self.comboBoxRegression.currentIndex() == 0:
                coefficients = self.horse.norm_coefficients
            else:
                coefficients = self.horse.nat_coefficients

            coefficients = np.round(coefficients, ROUND_TO)

            text_ends = [f'*x{i}' for i in range(FACTORS_NUMBER + 1)]
            # 2
            cur_factors_mult_index = 7
            for factor_index1 in range(1, FACTORS_NUMBER):
                for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER + 1):
                    text_ends.append(f'*x{factor_index1}x{factor_index2}')
                    cur_factors_mult_index += 1

            # 3
            for factor_index1 in range(1, FACTORS_NUMBER - 1):
                for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER):
                    for factor_index3 in range(factor_index2 + 1, FACTORS_NUMBER + 1):
                        text_ends.append(f'*x{factor_index1}x{factor_index2}x{factor_index3}')
                        cur_factors_mult_index += 1

            # 4
            for factor_index1 in range(1, FACTORS_NUMBER - 2):
                for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER - 1):
                    for factor_index3 in range(factor_index2 + 1, FACTORS_NUMBER):
                        for factor_index4 in range(factor_index3 + 1, FACTORS_NUMBER + 1):
                            text_ends.append(f'*x{factor_index1}x{factor_index2}x{factor_index3}x{factor_index4}')
                            cur_factors_mult_index += 1

            # 5
            for factor_index1 in range(1, FACTORS_NUMBER - 3):
                for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER - 2):
                    for factor_index3 in range(factor_index2 + 1, FACTORS_NUMBER - 1):
                        for factor_index4 in range(factor_index3 + 1, FACTORS_NUMBER):
                            for factor_index5 in range(factor_index4 + 1, FACTORS_NUMBER + 1):
                                text_ends.append(f'*x{factor_index1}x{factor_index2}x{factor_index3}x{factor_index4}'
                                                   f'x{factor_index5}')
                                cur_factors_mult_index += 1

            text_ends.append('*x1x2x3x4x5x6')

            linear_text = ' '.join([f'{coefficients[i]:+}{text_ends[i]}' for i in range(FACTORS_NUMBER + 1)])
            nonlinear_text = ' '.join([f'{coefficients[i]:+}{text_ends[i]}' for i in range(2 ** FACTORS_NUMBER)])

            self.linear.setText(linear_text)
            self.nonlinear.setText(nonlinear_text)
            self.check_button.setDisabled(False)
        except Exception as e:
            self.handle_error(repr(e))

    def run_PFE_experiment(self):
        try:
            cur_min_maxes = self.get_current_min_maxes()
            end_param = self.input_t.value()
            self.horse.set_cur_min_maxes(*cur_min_maxes, end_param)

            self.horse.run()
            self.show_PFE_results(0)

        except Exception as e:
            self.handle_error(repr(e))

    def handle_error(self, text):
        error_msg = QMessageBox()
        error_msg.setText('Ошибка!\n' + text)
        error_msg.show()
        error_msg.exec()


if __name__ == "__main__":
    app = QApplication([])
    application = mywindow()
    application.show()

    sys.exit(app.exec())
