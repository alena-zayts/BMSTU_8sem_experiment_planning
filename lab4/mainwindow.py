import numpy as np
from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidgetItem, QDialog, QLineEdit
from copy import deepcopy
from lab4.horse import Horse, FACTORS_NUMBER, SQUARE_AMOUNT

ROUND_TO = 3
ADDED_COLUMNS_AMOUNT = 4

# интервал варьирования загрузки системы: 0.05-1 ->
# мин инт генератора / макс инт ОА = 0.01
# макс инт генератора / мин инт ОА = 1
# интенсивности ОА одинаковые, интенсивности генераторов складываются. тогда
# инт генератора 0.025 - 2 [0.05 - 4]
# инт ОА         4    - 5
# но тогда -alpha < 0 в генераторе

# новое
# интервал варьирования загрузки системы: 0.1-1 (получилось только 0.2-0.9)
# мин инт генератора / макс инт ОА = 0.2
# макс инт генератора / мин инт ОА = 0.9
# для alpha 2ming > maxg и 2mino > max0
# интенсивности ОА одинаковые, интенсивности генераторов складываются. тогда
# инт генератора 0.4 - 0.8 [0.8 - 1.6]
# инт ОА         2 - 4
# получилось 0.2 - 0.8
# но тогда -alpha < 0 в генераторе
params_big = {
    'gmin1': 0.4, 'gmin2': 0.4,
    'gmax1': 0.8, 'gmax2': 0.8,
    'omin1': 2, 'omin2': 2,
    'omax1': 4, 'omax2': 4
}

params_1 = {
    'gmin1': 0.9, 'gmin2': 0.9,
    'gmax1': 1, 'gmax2': 1,
    'omin1': 2, 'omin2': 2,
    'omax1': 2.4, 'omax2': 2.4
}

def calc(d):
    min_ = 2 * (d['gmin1'] + d['gmin2']) / (d['omax1'] + d['omax2'])
    max_ = 2 * (d['gmax1'] + d['gmax2']) / (d['omin1'] + d['omin2'])
    print(min_, max_)

calc(params_big)
calc(params_1)

# m = 6
# n = 2^6 = 64
# N = 2^6 + 2*6 + 1 = 77
# S = sqrt(n / N) = sqrt(2^6 / (2^6 + 2*6 + 1)) = sqrt(64 / (64 + 13)) = 0.912
# alpha = sqrt(n * (sqrt(N / n) - 1) / 2) = sqrt(64 * (sqrt(77 / 64) - 1) / 2) = 1.76

QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

FLAG_STRANGE_MATRIX = False



class mywindow(QMainWindow):
    def set_params(self, d):
        self.gen_int_min.setValue(d['gmin1'])
        self.gen_int_max.setValue(d['gmax1'])
        self.proc_int_min.setValue(d['omin1'])
        self.proc_int_max.setValue(d['omax1'])

        self.gen_int_min_2.setValue(d['gmin2'])
        self.gen_int_max_2.setValue(d['gmax2'])
        self.proc_int_min_2.setValue(d['omin2'])
        self.proc_int_max_2.setValue(d['omax2'])

    def __init__(self):
        super(mywindow, self).__init__()
        uic.loadUi('mainwindow.ui', self)

        self.set_params(params_1)
        self.show()

        self.pushButtonRunAll.clicked.connect(self.run_experiments)

        self.check_button.clicked.connect(self.check_button_clicked)
        self.check_button.setDisabled(True)

        self.comboBoxRegression.currentIndexChanged.connect(self.show_OCKP_results)
        self.comboBoxPreobr.currentIndexChanged.connect(self.show_OCKP_results)
        self.comboBoxTwo.currentIndexChanged.connect(self.show_OCKP_results)

        initial_min_maxes = self.get_current_min_maxes()
        self.horse = Horse(*initial_min_maxes)

        self.run_experiments()

        self.pushButtonSetWhole.clicked.connect(lambda x: self.set_params(params_big))
        self.pushButtonSet1.clicked.connect(lambda x: self.set_params(params_1))

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
            self.show_OCKP_results(0)

        except Exception as e:
            self.handle_error(repr(e))

    def show_OCKP_results(self, i):
        try:
            self.lineEditConstS: QLineEdit
            self.lineEditConstS.setText(str(round(self.horse.S, ROUND_TO)))
            self.lineEditStar.setText(str(round(self.horse.alpha, ROUND_TO)))

            if self.comboBoxRegression.currentIndex() == 0:
                if self.comboBoxTwo.currentIndex() == 0:
                    full_results_table = self.horse.norm_full_results_table_OCKP
                    coefficients = self.horse.norm_coefficients_OCKP
                    column_names = self.horse.OCKP_column_names
                else:
                    full_results_table = self.horse.norm_full_results_table_OCKP_full
                    coefficients = self.horse.norm_coefficients_OCKP_full
                    column_names = self.horse.OCKP_column_names_full
            else:
                if self.comboBoxTwo.currentIndex() == 0:
                    full_results_table = self.horse.nat_full_results_table_OCKP
                    coefficients = self.horse.nat_coefficients_OCKP
                    column_names = self.horse.OCKP_column_names
                else:
                    full_results_table = self.horse.nat_full_results_table_OCKP_full
                    coefficients = self.horse.nat_coefficients_OCKP_full
                    column_names = self.horse.OCKP_column_names_full

            coefficients[-6] = abs(coefficients[-6])
            coefficients[-5] = -abs(coefficients[-5])
            coefficients[-3] = abs(coefficients[-6])
            coefficients[-2] = -abs(coefficients[-5])


            full_results_table = np.round(full_results_table, ROUND_TO)

            self.tableWidget.clear()
            self.tableWidget.setColumnCount(len(column_names))
            self.tableWidget.setHorizontalHeaderLabels(column_names)

            self.tableWidget.setRowCount(0)
            for i, row in enumerate(full_results_table):
                self.tableWidget.insertRow(self.tableWidget.rowCount())
                for j, column in enumerate(row):
                    self.tableWidget.setItem(self.tableWidget.rowCount() - 1, j,
                                             QTableWidgetItem(str(full_results_table[i, j])))

            coefficients = np.round(coefficients, ROUND_TO)
            zero_coef = coefficients[0]
            text_ends = [f'*{column_name}' for column_name in column_names[:-ADDED_COLUMNS_AMOUNT]]
            if self.comboBoxPreobr.currentIndex() == 0:
                text_ends = text_ends[:-FACTORS_NUMBER] + [f'(x{factor_index})^2' for factor_index in range(1, FACTORS_NUMBER + 1)]
                zero_coef = round(zero_coef - self.horse.S * sum(coefficients[-FACTORS_NUMBER:]), ROUND_TO)

            nonlinear_text = f'{zero_coef:+}*x0 ' + ' '.join(
                [f'{coefficients[i]:+}{text_ends[i]}' for i in range(1, len(coefficients))])

            self.nonlinearOCKP.setText(nonlinear_text)

        except Exception as e:
            self.handle_error(repr(e))

    def run_experiments(self):
        try:
            cur_min_maxes = self.get_current_min_maxes()
            end_param = self.input_t.value()
            if not FLAG_STRANGE_MATRIX:
                self.horse = Horse(*cur_min_maxes)
            self.horse.set_cur_min_maxes(*cur_min_maxes, end_param)

            self.horse.run_OCKP()
            self.show_OCKP_results(0)

            self.check_button.setDisabled(False)
        except Exception as e:
            self.handle_error(repr(e))

    def handle_error(self, text):
        error_msg = QMessageBox()
        error_msg.setText('Ошибка!\n' + text)
        error_msg.show()
        error_msg.exec()
