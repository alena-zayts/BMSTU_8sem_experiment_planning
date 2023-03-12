import sys
from typing import *

import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QRadioButton
from PyQt5 import uic

from lab1.generator import Generator
from lab1 import distributions
from lab1.modeller import Modeller
from lab1.processor import Processor
import time

show = True


class mywindow(QMainWindow):
    def __init__(self):
        super(mywindow, self).__init__()
        uic.loadUi('mainwindow.ui', self)
        self.show()

        self.pushButton_model.clicked.connect(self.modeling_button_clicked)
        self.pushButton_graph.clicked.connect(self.graph_button_clicked)

        if not show:
            if hasattr(self, 'res_theor_requests_amount'):
                self.res_theor_requests_amount.hide()
            if hasattr(self, 'res_theor_modelling_time'):
                self.res_theor_modelling_time.hide()
            if hasattr(self, 'res_theor_mean_time_in_queue'):
                self.res_theor_mean_time_in_queue.hide()

    def graph_button_clicked(self):
        start = time.time()

        # 2 минуты
        n_repeats = 100
        how_to_check = 'time'
        end_param = 1000

        # end_param = self.input_t.value()
        # if self.radioButton_t.isChecked():
        #     how_to_check = 'time'
        # else:
        #     how_to_check = 'requests'

        intens_generator = 1
        self.input_intens_generator.setValue(intens_generator)
        disp_processor = 0
        self.input_disp_processor.setValue(disp_processor)

        intens_p_step = 0.03
        p_theor_max = 1
        p_theor2 = 0.01

        p_theor_array = []
        t_mean_array = []
        while p_theor2 < p_theor_max + 0.001:

            intens_processor = intens_generator / p_theor2
            print(p_theor2)

            self.input_intens_processor.setValue(intens_processor)
            current_results = []

            for _ in range(n_repeats):
                generators, processors = self.create_generators_and_processors()
                model = Modeller(generators, processors)
                mean_time_in_queue = model.delta_t_modelling(how_to_check, end_param)['mean_time_in_queue']
                current_results.append(mean_time_in_queue)

            p_theor_array.append(p_theor2)
            t_mean_array.append(sum(current_results) / n_repeats)

            p_theor2 += intens_p_step

        end = time.time()
        print(f'Построение графика заняло {round(end - start)} секунд')
        plt.plot(p_theor_array, t_mean_array)
        plt.title('Зависимость среднего время ожидания в очереди от загрузки системы\n'
                  f'({how_to_check}={end_param})')
        plt.grid()
        plt.ylabel('Среднее время ожидания в очереди (модельное время)')
        plt.xlabel('Загрузка системы')
        plt.show()

    # def graph_button_clicked(self):
    #     start = time.time()
    #
    #     # 2 минуты
    #     n_repeats = 100
    #     how_to_check = 'time'
    #     end_param = 1000
    #
    #     # end_param = self.input_t.value()
    #     # if self.radioButton_t.isChecked():
    #     #     how_to_check = 'time'
    #     # else:
    #     #     how_to_check = 'requests'
    #
    #     intens_processor = 1
    #     disp_processor = 0
    #     self.input_intens_processor.setValue(intens_processor)
    #     self.input_disp_processor.setValue(disp_processor)
    #
    #     intens_generator = 0.01
    #     intens_generator_step = 0.03
    #     p_theor_max = 1
    #     p_theor2 = intens_generator / intens_processor
    #
    #     p_theor_array = []
    #     t_mean_array = []
    #     while p_theor2 <= p_theor_max + 0.001:
    #
    #         print(intens_generator)
    #
    #         self.input_intens_generator.setValue(intens_generator)
    #         current_results = []
    #
    #         for _ in range(n_repeats):
    #             generators, processors = self.create_generators_and_processors()
    #             model = Modeller(generators, processors)
    #             mean_time_in_queue = model.time_based_modelling(how_to_check, end_param)['mean_time_in_queue']
    #             current_results.append(mean_time_in_queue)
    #
    #         p_theor_array.append(p_theor2)
    #         t_mean_array.append(sum(current_results) / n_repeats)
    #
    #         intens_generator += intens_generator_step
    #         p_theor2 = intens_generator / intens_processor
    #
    #     end = time.time()
    #     print(f'Построение графика заняло {round(end - start)} секунд')
    #     plt.plot(p_theor_array, t_mean_array)
    #     plt.title('Зависимость среднего время ожидания в очереди от загрузки системы\n'
    #               f'({how_to_check}={end_param})')
    #     plt.grid()
    #     plt.ylabel('Среднее время ожидания в очереди (модельное время)')
    #     plt.xlabel('Загрузка системы')
    #     plt.show()

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

            result = model.delta_t_modelling(how_to_check, end_param)

            generator_intensity = self.input_intens_generator.value()
            processor_intensity = self.input_intens_processor.value()
            p_theor = generator_intensity / processor_intensity
            self.res_theor_zagr.setText(str(round(p_theor, round_to)))

            p_fact = result['p_fact']
            self.res_fact_zagr.setText(str(round(p_fact, round_to)))

            self.res_exp_requests_amount.setText(str(result['processed_requests']))
            self.res_exp_modelling_time.setText(str(round(result['modeling_time'], round_to)))
            self.res_exp_mean_time_in_queue.setText(str(round(result['mean_time_in_queue'], round_to)))

            if show:
                # TODO
                if p_theor < 1:
                    if how_to_check == 'requests':
                        res_theor_requests_amount = str(end_param)

                        res_theor_modelling_time = (1 / max([generator_intensity, processor_intensity]) +
                                                    end_param / min([generator_intensity, processor_intensity]))
                        res_theor_modelling_time = str(round(res_theor_modelling_time))

                    else:
                        res_theor_modelling_time = str(end_param)

                        res_theor_requests_amount = ((end_param - 1 / max([generator_intensity, processor_intensity]))
                                                     * min([generator_intensity, processor_intensity]))
                        res_theor_requests_amount = str(int(res_theor_requests_amount))

                    # https://studfile.net/preview/9196366/page:5/
                    # res_theor_mean_time_in_queue = 1 / processor_intensity / (1 - p_theor)
                    # https://en.wikipedia.org/wiki/M/D/1_queue
                    res_theor_mean_time_in_queue = p_theor / (2 * processor_intensity * (1 - p_theor))
                    res_theor_mean_time_in_queue = str(round(res_theor_mean_time_in_queue, round_to))

                else:
                    res_theor_mean_time_in_queue = ''
                    res_theor_requests_amount = ''
                    res_theor_modelling_time = ''

                self.res_theor_requests_amount.setText(res_theor_requests_amount)
                self.res_theor_modelling_time.setText(res_theor_modelling_time)
                self.res_theor_mean_time_in_queue.setText(res_theor_mean_time_in_queue)




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
