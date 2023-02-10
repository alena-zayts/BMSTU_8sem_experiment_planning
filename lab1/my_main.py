import sys
from typing import *

import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QRadioButton
from PyQt5 import uic

from lab1.generator import Generator
from lab1 import distributions
from lab1.modeller import Modeller
from lab1.processor import Processor


class mywindow(QMainWindow):
    def __init__(self):
        super(mywindow, self).__init__()
        uic.loadUi('mainwindow.ui', self)
        self.show()

        self.pushButton_model.clicked.connect(self.modeling_button_clicked)
        self.pushButton_graph.clicked.connect(self.graph_button_clicked)

    def graph_button_clicked(self):
        n_repeats = 10

        # how_to_check = 'requests'
        # end_param = 1000
        end_param = self.input_t.value()
        self.radioButton_t: QRadioButton
        if self.radioButton_t.isChecked():
            how_to_check = 'time'
        else:
            how_to_check = 'requests'

        intens_processor = 1
        disp_processor = 0
        self.input_intens_processor.setValue(intens_processor)
        self.input_disp_processor.setValue(disp_processor)

        intens_generator = 0.02
        intens_generator_step = 0.02
        p_theor_max = 1.2
        p_theor2 = intens_generator / intens_processor

        p_theor_array = []
        t_mean_array = []
        while p_theor2 <= p_theor_max:

            print(intens_generator)

            self.input_intens_generator.setValue(intens_generator)
            current_results = []

            for _ in range(n_repeats):
                generators, processors = self.create_generators_and_processors()
                model = Modeller(generators, processors)
                mean_time_in_queue = model.time_based_modelling(how_to_check, end_param)['mean_time_in_queue']
                current_results.append(mean_time_in_queue)

            p_theor_array.append(p_theor2)
            t_mean_array.append(sum(current_results) / n_repeats)

            intens_generator += intens_generator_step
            p_theor2 = intens_generator / intens_processor

        plt.plot(p_theor_array, t_mean_array)
        plt.title('Зависимость среднего время ожидания в очереди от загрузки системы\n'
                  f'({how_to_check}={end_param})')
        plt.grid()
        plt.ylabel('Среднее время ожидания в очереди (модельное время)')
        plt.xlabel('Загрузка системы')
        plt.show()

    def create_generators_and_processors(self) -> (List[Generator], List[Processor]):
        generators = []
        processors = []

        # TODO проверить
        # матожидание экспоненциального распределения = 1 / lambda
        # интенсивность = 1 / матожидание экспоненциального распределения
        # lambda = интенсивность
        generator_intensity = self.input_intens_generator.value()
        lambda_ = 1 / generator_intensity
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
        try:
            round_to = 3
            end_param = self.input_t.value()
            self.radioButton_t: QRadioButton
            if self.radioButton_t.isChecked():
                how_to_check = 'time'
            else:
                how_to_check = 'requests'

            generators, processors = self.create_generators_and_processors()
            model = Modeller(generators, processors)

            result = model.time_based_modelling(how_to_check, end_param)

            generator_intensity = self.input_intens_generator.value()
            processor_intensity = self.input_intens_processor.value()
            p_theor = generator_intensity / processor_intensity
            self.res_theor_zagr.setText(str(round(p_theor, round_to)))

            p_fact = result['p_fact']
            self.res_fact_zagr.setText(str(round(p_fact, round_to)))

            # TODO надо ли
            # self.ui.teor_time.setText(str(round(p_theor / (1 - p_theor) / generator_intensity, r)))
            # self.ui.fact_time.setText(str(round(result[7], 4)))

            self.res_exp_requests_amount.setText(str(result['processed_requests']))
            self.res_exp_modelling_time.setText(str(round(result['modeling_time'], round_to)))
            self.res_exp_mean_time_in_queue.setText(str(round(result['mean_time_in_queue'], round_to)))
            self.res_exp_mean_time_in_smo.setText(str(round(result['mean_time_in_smo'], round_to)))

            # TODO
            if how_to_check == 'requests':
                self.res_theor_requests_amount.setText(str(end_param))
                res_theor_modelling_time = (1 / max([generator_intensity, processor_intensity]) +
                                            end_param / min([generator_intensity, processor_intensity]))
                self.res_theor_modelling_time.setText(str(round(res_theor_modelling_time, round_to)))
            else:
                self.res_theor_modelling_time.setText(str(end_param))
                res_theor_requests_amount = (end_param - 1 / max([generator_intensity, processor_intensity]) +
                                             end_param * min([generator_intensity, processor_intensity]))
                self.res_theor_requests_amount.setText(str(round(res_theor_requests_amount, round_to)))

            self.res_theor_mean_time_in_queue.setText(str(round(result['mean_time_in_queue'], round_to)))
            self.res_theor_mean_time_in_smo.setText(str(round(result['mean_time_in_smo'], round_to)))

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

# TODO загруженность, среднее время пребывания в системе, общее время моделирования, число обработанных заявок
