import numpy as np
from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidgetItem, QDialog

from lab3.horse import Horse, FACTORS_NUMBER

ROUND_TO = 3

# интервал варьирования загрузки системы: 0.05-0.5 ->
# мин инт генератора / макс инт ОА = 0.01
# макс инт генератора / мин инт ОА = 0.5

# интенсивности ОА одинаковые, интенсивности генераторов складываются. тогда
# инт генератора 0.025 - 1 [0.05 - 2]
# инт ОА         4    - 5


QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

FLAG_STRANGE_MATRIX = False
FLAG_SHOW_AAA = True
FLAG_HIDE_4 = False
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
        if FLAG_SHOW_AAA:
            self.pushButtonDFE4.clicked.connect(self.show_DFE4_results_AAA)
            self.pushButtonDFE2.clicked.connect(self.show_DFE2_results_AAA)
        else:
            self.pushButtonDFE4.clicked.connect(self.show_DFE4_results)
            self.pushButtonDFE2.clicked.connect(self.show_DFE2_results)

        self.check_button.clicked.connect(self.check_button_clicked)
        self.check_button.setDisabled(True)
        self.pushButtonPFE.setDisabled(True)
        self.pushButtonDFE4.setDisabled(True)
        self.pushButtonDFE2.setDisabled(True)

        self.tableDialogPFE = TableDialog()
        self.tableDialogDFE4 = TableDialog()
        self.tableDialogDFE2 = TableDialog()

        self.tableDialogPFE.setWindowTitle('Матрица планирования ПФЭ')
        self.tableDialogDFE4.setWindowTitle('Матрица планирования ДФЭ (1/4)')
        self.tableDialogDFE2.setWindowTitle('Матрица планирования ДФЭ (1/2)')

        g = self.tableDialogPFE.geometry()
        g.setY(0)
        self.tableDialogPFE.setGeometry(g)

        g = self.tableDialogDFE2.geometry()
        g.setY(100)
        self.tableDialogDFE2.setGeometry(g)

        g = self.tableDialogDFE4.geometry()
        g.setY(200)
        self.tableDialogDFE4.setGeometry(g)

        self.tableDialogPFE.comboBoxMatrix.currentIndexChanged.connect(self.show_PFE_results)

        if FLAG_SHOW_AAA:
            self.tableDialogDFE4.comboBoxMatrix.currentIndexChanged.connect(self.show_DFE4_results_AAA)
            self.tableDialogDFE2.comboBoxMatrix.currentIndexChanged.connect(self.show_DFE2_results_AAA)
        else:
            self.tableDialogDFE4.comboBoxMatrix.currentIndexChanged.connect(self.show_DFE4_results)
            self.tableDialogDFE2.comboBoxMatrix.currentIndexChanged.connect(self.show_DFE2_results)

        self.comboBoxRegression.currentIndexChanged.connect(self.show_PFE_results)
        if FLAG_SHOW_AAA:
            self.comboBoxRegression.currentIndexChanged.connect(self.show_DFE2_results_AAA)
            self.comboBoxRegression.currentIndexChanged.connect(self.show_DFE4_results_AAA)
        else:
            self.comboBoxRegression.currentIndexChanged.connect(self.show_DFE2_results)
            self.comboBoxRegression.currentIndexChanged.connect(self.show_DFE4_results)

        initial_min_maxes = self.get_current_min_maxes()
        self.horse = Horse(*initial_min_maxes)

        if FLAG_HIDE_4:
            self.pushButtonDFE4.hide()
            self.label_18.hide()
            self.label_39.hide()
            self.label_40.hide()
            self.linearDFE4.hide()
            self.nonlinearDFE4.hide()

            g = self.tableDialogDFE4.geometry()
            g.setY(1500)
            self.tableDialogDFE4.setGeometry(g)
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
            if FLAG_SHOW_AAA:
                self.show_DFE2_results_AAA(0)
                self.show_DFE4_results_AAA(0)
            else:
                self.show_DFE2_results(0)
                self.show_DFE4_results(0)

        except Exception as e:
            self.handle_error(repr(e))

    def show_PFE_results(self, i):
        try:
            if self.tableDialogPFE.comboBoxMatrix.currentIndex() == 0:
                full_results_table = self.horse.norm_full_results_table_PFE
            else:
                if FLAG_REAL:
                    full_results_table = self.horse.real_nat_full_results_table_PFE
                else:
                    full_results_table = self.horse.nat_full_results_table_PFE

            full_results_table = np.round(full_results_table, ROUND_TO)

            self.tableDialogPFE.tableWidget.clear()
            self.tableDialogPFE.tableWidget.setColumnCount(len(self.horse.PFE_column_names))
            self.tableDialogPFE.tableWidget.setHorizontalHeaderLabels(self.horse.PFE_column_names)

            self.tableDialogPFE.tableWidget.setRowCount(0)
            for i, row in enumerate(full_results_table):
                self.tableDialogPFE.tableWidget.insertRow(self.tableDialogPFE.tableWidget.rowCount())
                for j, column in enumerate(row):
                    self.tableDialogPFE.tableWidget.setItem(self.tableDialogPFE.tableWidget.rowCount() - 1, j,
                                                            QTableWidgetItem(str(full_results_table[i, j])))

            if self.comboBoxRegression.currentIndex() == 0:
                coefficients = self.horse.norm_coefficients_PFE
            else:
                if FLAG_REAL:
                    coefficients = self.horse.real_nat_coefficients_PFE[:22]
                else:
                    coefficients = self.horse.nat_coefficients_PFE

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

            self.linearPFE.setText(linear_text)
            self.nonlinearPFE.setText(nonlinear_text)

            self.tableDialogPFE.show()
        except Exception as e:
            self.handle_error(repr(e))

    def show_DFE4_results_AAA(self, i):
        try:
            if self.tableDialogDFE4.comboBoxMatrix.currentIndex() == 0:
                full_results_table = self.horse.norm_full_results_table_DFE4_AAA
            else:
                if FLAG_REAL:
                    full_results_table = self.horse.real_nat_full_results_table_DFE4_AAA
                else:
                    full_results_table = self.horse.nat_full_results_table_DFE4_AAA


            full_results_table = np.round(full_results_table, ROUND_TO)

            self.tableDialogDFE4.tableWidget.setColumnCount(len(self.horse.DFE4_column_names_AAA))
            self.tableDialogDFE4.tableWidget.setHorizontalHeaderLabels(self.horse.DFE4_column_names_AAA)
            self.tableDialogDFE4.tableWidget.setRowCount(0)

            for i, row in enumerate(full_results_table):
                self.tableDialogDFE4.tableWidget.insertRow(self.tableDialogDFE4.tableWidget.rowCount())
                for j, column in enumerate(row):
                    self.tableDialogDFE4.tableWidget.setItem(self.tableDialogDFE4.tableWidget.rowCount() - 1, j,
                                                             QTableWidgetItem(str(full_results_table[i, j])))

            if self.comboBoxRegression.currentIndex() == 0:
                coefficients = self.horse.norm_coefficients_DFE4_AAA
            else:
                if FLAG_REAL:
                    coefficients = self.horse.real_nat_coefficients_DFE4_AAA[:22]
                else:
                    coefficients = self.horse.nat_coefficients_DFE4_AAA

            coefficients = np.round(coefficients, ROUND_TO)

            text_ends = [f'*x{i}' for i in range(FACTORS_NUMBER + 1)]
            # 2
            cur_factors_mult_index = 7
            for factor_index1 in range(1, FACTORS_NUMBER):
                for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER + 1):
                    text_ends.append(f'*x{factor_index1}x{factor_index2}')
                    cur_factors_mult_index += 1

            linear_text = ' '.join([f'{coefficients[i]:+}{text_ends[i]}' for i in range(FACTORS_NUMBER + 1)])
            nonlinear_text = ' '.join([f'{coefficients[i]:+}{text_ends[i]}' for i in range(len(coefficients))])

            self.linearDFE4.setText(linear_text)
            self.nonlinearDFE4.setText(nonlinear_text)
            self.tableDialogDFE4.show()
        except Exception as e:
            self.handle_error(repr(e))


    def show_DFE2_results_AAA(self, i):
        try:
            if self.tableDialogDFE2.comboBoxMatrix.currentIndex() == 0:
                full_results_table = self.horse.norm_full_results_table_DFE2_AAA
            else:
                if FLAG_REAL:
                    full_results_table = self.horse.real_nat_full_results_table_DFE2_AAA
                else:
                    full_results_table = self.horse.nat_full_results_table_DFE2_AAA

            full_results_table = np.round(full_results_table, ROUND_TO)

            self.tableDialogDFE2.tableWidget.setColumnCount(len(self.horse.DFE2_column_names_AAA))
            self.tableDialogDFE2.tableWidget.setHorizontalHeaderLabels(self.horse.DFE2_column_names_AAA)
            self.tableDialogDFE2.tableWidget.setRowCount(0)

            for i, row in enumerate(full_results_table):
                self.tableDialogDFE2.tableWidget.insertRow(self.tableDialogDFE2.tableWidget.rowCount())
                for j, column in enumerate(row):
                    self.tableDialogDFE2.tableWidget.setItem(self.tableDialogDFE2.tableWidget.rowCount() - 1, j,
                                                             QTableWidgetItem(str(full_results_table[i, j])))

            if self.comboBoxRegression.currentIndex() == 0:
                coefficients = self.horse.norm_coefficients_DFE2_AAA
            else:
                if FLAG_REAL:
                    coefficients = self.horse.real_nat_coefficients_DFE2_AAA[:22]
                else:
                    coefficients = self.horse.nat_coefficients_DFE2_AAA


            coefficients = np.round(coefficients, ROUND_TO)

            text_ends = [f'*x{i}' for i in range(FACTORS_NUMBER + 1)]
            # 2
            cur_factors_mult_index = 7
            for factor_index1 in range(1, FACTORS_NUMBER):
                for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER + 1):
                    text_ends.append(f'*x{factor_index1}x{factor_index2}')
                    cur_factors_mult_index += 1

            linear_text = ' '.join([f'{coefficients[i]:+}{text_ends[i]}' for i in range(FACTORS_NUMBER + 1)])
            nonlinear_text = ' '.join([f'{coefficients[i]:+}{text_ends[i]}' for i in range(len(coefficients))])

            self.linearDFE2.setText(linear_text)
            self.nonlinearDFE2.setText(nonlinear_text)
            self.tableDialogDFE2.show()
        except Exception as e:
            self.handle_error(repr(e))

    def show_DFE4_results(self, i):
        try:
            if self.tableDialogDFE4.comboBoxMatrix.currentIndex() == 0:
                full_results_table = self.horse.norm_full_results_table_DFE4
            else:
                if FLAG_REAL:
                    full_results_table = self.horse.real_nat_full_results_table_DFE4
                else:
                    full_results_table = self.horse.nat_full_results_table_DFE4

            full_results_table = np.round(full_results_table, ROUND_TO)

            self.tableDialogDFE4.tableWidget.setColumnCount(len(self.horse.DFE4_column_names))
            self.tableDialogDFE4.tableWidget.setHorizontalHeaderLabels(self.horse.DFE4_column_names)
            self.tableDialogDFE4.tableWidget.setRowCount(0)

            for i, row in enumerate(full_results_table):
                self.tableDialogDFE4.tableWidget.insertRow(self.tableDialogDFE4.tableWidget.rowCount())
                for j, column in enumerate(row):
                    self.tableDialogDFE4.tableWidget.setItem(self.tableDialogDFE4.tableWidget.rowCount() - 1, j,
                                                             QTableWidgetItem(str(full_results_table[i, j])))

            if self.comboBoxRegression.currentIndex() == 0:
                coefficients = self.horse.norm_coefficients_DFE4
            else:
                if FLAG_REAL:
                    coefficients = self.horse.real_nat_coefficients_DFE4
                else:
                    coefficients = self.horse.nat_coefficients_DFE4

            coefficients = np.round(coefficients, ROUND_TO)

            text_ends = [f'*x{i}' for i in range(FACTORS_NUMBER + 1)]
            # 2
            cur_factors_mult_index = 7
            for factor_index1 in range(1, FACTORS_NUMBER):
                for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER + 1):
                    text_ends.append(f'*x{factor_index1}x{factor_index2}')
                    cur_factors_mult_index += 1

            linear_text = ' '.join([f'{coefficients[self.horse.DFE4_map_coefficients[i]]:+}{text_ends[i]}' for i in
                                    range(FACTORS_NUMBER + 1)])
            nonlinear_text = ' '.join(
                [f'{coefficients[self.horse.DFE4_map_coefficients[i]]:+}{text_ends[i]}' for i in range(len(text_ends))])

            self.linearDFE4.setText(linear_text)
            self.nonlinearDFE4.setText(nonlinear_text)
            self.tableDialogDFE4.show()
        except Exception as e:
            self.handle_error(repr(e))

    def show_DFE2_results(self, i):
        try:
            if self.tableDialogDFE2.comboBoxMatrix.currentIndex() == 0:
                full_results_table = self.horse.norm_full_results_table_DFE2
            else:
                if FLAG_REAL:
                    full_results_table = self.horse.real_nat_full_results_table_DFE2
                else:
                    full_results_table = self.horse.nat_full_results_table_DFE2

            full_results_table = np.round(full_results_table, ROUND_TO)

            self.tableDialogDFE2.tableWidget.setColumnCount(len(self.horse.DFE2_column_names))
            self.tableDialogDFE2.tableWidget.setHorizontalHeaderLabels(self.horse.DFE2_column_names)
            self.tableDialogDFE2.tableWidget.setRowCount(0)

            for i, row in enumerate(full_results_table):
                self.tableDialogDFE2.tableWidget.insertRow(self.tableDialogDFE2.tableWidget.rowCount())
                for j, column in enumerate(row):
                    self.tableDialogDFE2.tableWidget.setItem(self.tableDialogDFE2.tableWidget.rowCount() - 1, j,
                                                             QTableWidgetItem(str(full_results_table[i, j])))

            if self.comboBoxRegression.currentIndex() == 0:
                coefficients = self.horse.norm_coefficients_DFE2
            else:
                if FLAG_REAL:
                    coefficients = self.horse.real_nat_coefficients_DFE2
                else:
                    coefficients = self.horse.nat_coefficients_DFE2


            coefficients = np.round(coefficients, ROUND_TO)

            text_ends = [f'*x{i}' for i in range(FACTORS_NUMBER + 1)]
            # 2
            cur_factors_mult_index = 7
            for factor_index1 in range(1, FACTORS_NUMBER):
                for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER + 1):
                    text_ends.append(f'*x{factor_index1}x{factor_index2}')
                    cur_factors_mult_index += 1

            linear_text = ' '.join([f'{coefficients[self.horse.DFE2_map_coefficients[i]]:+}{text_ends[i]}' for i in
                                    range(FACTORS_NUMBER + 1)])
            nonlinear_text = ' '.join(
                [f'{coefficients[self.horse.DFE2_map_coefficients[i]]:+}{text_ends[i]}' for i in range(len(text_ends))])

            self.linearDFE2.setText(linear_text)
            self.nonlinearDFE2.setText(nonlinear_text)
            self.tableDialogDFE2.show()
        except Exception as e:
            self.handle_error(repr(e))

    def run_experiments(self):
        try:
            cur_min_maxes = self.get_current_min_maxes()
            end_param = self.input_t.value()

            if not FLAG_STRANGE_MATRIX:
                self.horse = Horse(*cur_min_maxes)

            self.horse.set_cur_min_maxes(*cur_min_maxes, end_param)

            self.horse.run_PFE()
            self.show_PFE_results(0)

            self.horse.run_DFE4()
            self.horse.run_DFE2()

            if FLAG_SHOW_AAA:
                self.show_DFE4_results_AAA(0)
                self.show_DFE2_results_AAA(0)
            else:
                self.show_DFE4_results(0)
                self.show_DFE2_results(0)

            self.check_button.setDisabled(False)
            self.pushButtonPFE.setDisabled(False)
            self.pushButtonDFE4.setDisabled(False)
            self.pushButtonDFE2.setDisabled(False)
        except Exception as e:
            self.handle_error(repr(e))

    def handle_error(self, text):
        error_msg = QMessageBox()
        error_msg.setText('Ошибка!\n' + text)
        error_msg.show()
        error_msg.exec()
