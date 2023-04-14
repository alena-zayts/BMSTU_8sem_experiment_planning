import numpy as np
from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidgetItem, QDialog

from lab4.horse import Horse, FACTORS_NUMBER

ROUND_TO = 3
# PFE = ОЦКП

# интервал варьирования загрузки системы: 0.05-1 ->
# мин инт генератора / макс инт ОА = 0.01
# макс инт генератора / мин инт ОА = 1

# интенсивности ОА одинаковые, интенсивности генераторов складываются. тогда
# инт генератора 0.025 - 2 [0.05 - 4]
# инт ОА         4    - 5


QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

FLAG_STRANGE_MATRIX = False
FLAG_REAL = False


class TableDialog(QDialog):
    def __init__(self):
        super(TableDialog, self).__init__()
        uic.loadUi('dialog.ui', self)


class mywindow(QMainWindow):
    def __init__(self):
        super(mywindow, self).__init__()
        uic.loadUi('mainwindow.ui', self)

        self.show()

        self.pushButtonRunAll.clicked.connect(self.run_experiments)
        self.pushButtonPFE.clicked.connect(self.show_PFE_results)

        self.check_button.clicked.connect(self.check_button_clicked)
        self.check_button.setDisabled(True)
        self.pushButtonPFE.setDisabled(True)

        self.tableDialogPFE = TableDialog()
        self.tableDialogPFE.setWindowTitle('Матрица планирования ОЦКП')
        self.tableDialogPFE.comboBoxMatrix.currentIndexChanged.connect(self.show_PFE_results)
        self.comboBoxRegression.currentIndexChanged.connect(self.show_PFE_results)

        initial_min_maxes = self.get_current_min_maxes()
        self.horse = Horse(*initial_min_maxes)

        self.run_experiments()

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
            if self.tableDialogPFE.comboBoxMatrix.currentIndex() == 0:
                full_results_table = self.horse.norm_full_results_table_OCKP
            else:
                if FLAG_REAL:
                    full_results_table = self.horse.real_nat_full_results_table_OCKP
                else:
                    full_results_table = self.horse.nat_full_results_table_OCKP

            full_results_table = np.round(full_results_table, ROUND_TO)

            self.tableDialogPFE.tableWidget.clear()
            self.tableDialogPFE.tableWidget.setColumnCount(len(self.horse.OCKP_column_names))
            self.tableDialogPFE.tableWidget.setHorizontalHeaderLabels(self.horse.OCKP_column_names)

            self.tableDialogPFE.tableWidget.setRowCount(0)
            for i, row in enumerate(full_results_table):
                self.tableDialogPFE.tableWidget.insertRow(self.tableDialogPFE.tableWidget.rowCount())
                for j, column in enumerate(row):
                    self.tableDialogPFE.tableWidget.setItem(self.tableDialogPFE.tableWidget.rowCount() - 1, j,
                                                            QTableWidgetItem(str(full_results_table[i, j])))

            if self.comboBoxRegression.currentIndex() == 0:
                coefficients = self.horse.norm_coefficients_OCKP
            else:
                if FLAG_REAL:
                    coefficients = self.horse.real_nat_coefficients_OCKP[:22]
                else:
                    coefficients = self.horse.nat_coefficients_OCKP

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
            nonlinear_text = ' '.join([f'{coefficients[i]:+}{text_ends[i]}' for i in range(len(coefficients))])

            self.nonlinearPFE.setText(nonlinear_text)

            self.tableDialogPFE.show()
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
            self.show_PFE_results(0)

            self.check_button.setDisabled(False)
            self.pushButtonPFE.setDisabled(False)
        except Exception as e:
            self.handle_error(repr(e))

    def handle_error(self, text):
        error_msg = QMessageBox()
        error_msg.setText('Ошибка!\n' + text)
        error_msg.show()
        error_msg.exec()
