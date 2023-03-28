import numpy as np
from itertools import combinations
from math import factorial
from collections import defaultdict
from copy import deepcopy

from lab3.queue import distributions
from lab3.queue.generator import Generator
from lab3.queue.modeller import Modeller
from lab3.queue.processor import Processor

FACTORS_NUMBER = 6
M_SIZE = 2 ** FACTORS_NUMBER
LIN_COEFS_AMOUNT = FACTORS_NUMBER + 1
NONLIN_COEFS_AMOUNT = M_SIZE

FACTORS_NUMBER_D4 = 4
M_SIZE_D4 = 2 ** FACTORS_NUMBER_D4
LIN_COEFS_AMOUNT_D4 = FACTORS_NUMBER_D4 + 1
NONLIN_COEFS_AMOUNT_D4 = M_SIZE_D4

FACTORS_NUMBER_D2 = 5
M_SIZE_D2 = 2 ** FACTORS_NUMBER_D2
LIN_COEFS_AMOUNT_D2 = FACTORS_NUMBER_D2 + 1
NONLIN_COEFS_AMOUNT_D2 = M_SIZE_D2

N_REPEATS = 3

EPS = 1e-10


class Horse:
    # x1 - gen_int
    # x2 - proc_int
    # x3 - proc_var
    # x4 - gen_int2
    # x5 - proc_int2
    # x6 - proc_var2

    def __init__(self, gen_int_min, gen_int_max, proc_int_min, proc_int_max, proc_var_min, proc_var_max,
                 gen_int_min2, gen_int_max2, proc_int_min2, proc_int_max2, proc_var_min2, proc_var_max2):
        self.global_gen_int_min = gen_int_min
        self.global_gen_int_max = gen_int_max
        self.global_proc_int_min = proc_int_min
        self.global_proc_int_max = proc_int_max
        self.global_proc_var_min = proc_var_min
        self.global_proc_var_max = proc_var_max

        self.global_gen_int_min2 = gen_int_min2
        self.global_gen_int_max2 = gen_int_max2
        self.global_proc_int_min2 = proc_int_min2
        self.global_proc_int_max2 = proc_int_max2
        self.global_proc_var_min2 = proc_var_min2
        self.global_proc_var_max2 = proc_var_max2

        self.min_maxes_global = [
            [gen_int_min, gen_int_max], [proc_int_min, proc_int_max], [proc_var_min, proc_var_max],
            [gen_int_min2, gen_int_max2], [proc_int_min2, proc_int_max2], [proc_var_min2, proc_var_max2]
        ]

        # self.pfe_coefficients = []

    def set_cur_min_maxes(self, gen_int_min, gen_int_max, proc_int_min, proc_int_max, proc_var_min, proc_var_max,
                          gen_int_min2, gen_int_max2, proc_int_min2, proc_int_max2, proc_var_min2, proc_var_max2,
                          requests_amount):
        self.gen_int_min = gen_int_min
        self.gen_int_max = gen_int_max
        self.proc_int_min = proc_int_min
        self.proc_int_max = proc_int_max
        self.proc_var_min = proc_var_min
        self.proc_var_max = proc_var_max

        self.gen_int_min2 = gen_int_min2
        self.gen_int_max2 = gen_int_max2
        self.proc_int_min2 = proc_int_min2
        self.proc_int_max2 = proc_int_max2
        self.proc_var_min2 = proc_var_min2
        self.proc_var_max2 = proc_var_max2

        self.requests_amount = requests_amount
        self.min_maxes_nat = [
            [gen_int_min, gen_int_max], [proc_int_min, proc_int_max], [proc_var_min, proc_var_max],
            [gen_int_min2, gen_int_max2], [proc_int_min2, proc_int_max2], [proc_var_min2, proc_var_max2]
        ]
        self.min_maxes_norm = [
            [self.norm_factor_from_nat(self.min_maxes_nat[i][0], self.min_maxes_global[i][0],
                                       self.min_maxes_global[i][1]),
             self.norm_factor_from_nat(self.min_maxes_nat[i][1], self.min_maxes_global[i][0],
                                       self.min_maxes_global[i][1])]
            for i in range(len(self.min_maxes_global))
        ]

        self.create_PFE_plan_matrix()
        self.create_DFE4_plan_matrix()
        self.create_DFE2_plan_matrix()

    def nat_factor_from_norm(self, x_norm, xmin_nat, xmax_nat):
        return x_norm * (xmax_nat - xmin_nat) / 2 + (xmax_nat + xmin_nat) / 2

    def norm_factor_from_nat(self, x_nat, xmin_nat, xmax_nat):
        x0 = (xmin_nat + xmax_nat) / 2
        interval = (xmax_nat - xmin_nat) / 2
        return (x_nat - x0) / interval

    def convert_params(self, gen_int, proc_int, proc_var):
        if gen_int == 0:
            gen_int = EPS
        if proc_int == 0:
            proc_int = EPS

        lambda_, mu, sigma = gen_int, 1 / proc_int, proc_var

        return lambda_, mu, sigma

    def create_PFE_plan_matrix(self):  # min_maxes: [[[min1, max1], [min2, max2], ...]
        xs_column_names = [f'x{factor_index}' for factor_index in range(FACTORS_NUMBER + 1)] + \
                          [''] * (M_SIZE - FACTORS_NUMBER - 1)

        # fill everything with minimums
        natural_row = ([1] +  # x0
                       [self.min_maxes_nat[factor_index][0] for factor_index in range(FACTORS_NUMBER)] +
                       [1] * (M_SIZE - FACTORS_NUMBER - 1))  # temporary (just to give space)
        natural_matrix = np.array([natural_row for _ in range(M_SIZE)])
        norm_row = ([1] +  # x0
                    [self.min_maxes_norm[factor_index][0] for factor_index in range(FACTORS_NUMBER)] +
                    [1] * (M_SIZE - FACTORS_NUMBER - 1))  # temporary (just to give space)
        norm_matrix = np.array([norm_row for _ in range(M_SIZE)])

        for factor_index in range(1, FACTORS_NUMBER + 1):
            period = pow(2, FACTORS_NUMBER - factor_index)
            for start_minus in range(period, M_SIZE, 2 * period):
                for row_number in range(start_minus, start_minus + period):
                    natural_matrix[row_number, factor_index] = self.min_maxes_nat[factor_index - 1][1]  # add maxes
                    norm_matrix[row_number, factor_index] = self.min_maxes_norm[factor_index - 1][1]

        # 2
        cur_factors_mult_index = 7
        for factor_index1 in range(1, FACTORS_NUMBER):
            for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER + 1):
                xs_column_names[cur_factors_mult_index] = f'x{factor_index1}x{factor_index2}'
                natural_matrix[:, cur_factors_mult_index] = natural_matrix[:, factor_index1] * natural_matrix[:,
                                                                                               factor_index2]
                norm_matrix[:, cur_factors_mult_index] = norm_matrix[:, factor_index1] * norm_matrix[:, factor_index2]
                cur_factors_mult_index += 1

        # 3
        for factor_index1 in range(1, FACTORS_NUMBER - 1):
            for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER):
                for factor_index3 in range(factor_index2 + 1, FACTORS_NUMBER + 1):
                    xs_column_names[cur_factors_mult_index] = f'x{factor_index1}x{factor_index2}x{factor_index3}'
                    natural_matrix[:, cur_factors_mult_index] = (
                            natural_matrix[:, factor_index1] * natural_matrix[:, factor_index2] *
                            natural_matrix[:, factor_index3])
                    norm_matrix[:, cur_factors_mult_index] = (
                            norm_matrix[:, factor_index1] * norm_matrix[:, factor_index2] *
                            norm_matrix[:, factor_index3])
                    cur_factors_mult_index += 1

        # 4
        for factor_index1 in range(1, FACTORS_NUMBER - 2):
            for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER - 1):
                for factor_index3 in range(factor_index2 + 1, FACTORS_NUMBER):
                    for factor_index4 in range(factor_index3 + 1, FACTORS_NUMBER + 1):
                        xs_column_names[cur_factors_mult_index] = f'x{factor_index1}x{factor_index2}' \
                                                                  f'x{factor_index3}x{factor_index4}'
                        natural_matrix[:, cur_factors_mult_index] = (
                                natural_matrix[:, factor_index1] * natural_matrix[:, factor_index2] *
                                natural_matrix[:, factor_index3] * natural_matrix[:, factor_index4])
                        norm_matrix[:, cur_factors_mult_index] = (
                                norm_matrix[:, factor_index1] * norm_matrix[:, factor_index2] *
                                norm_matrix[:, factor_index3] * norm_matrix[:, factor_index4])
                        cur_factors_mult_index += 1

        # 5
        for factor_index1 in range(1, FACTORS_NUMBER - 3):
            for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER - 2):
                for factor_index3 in range(factor_index2 + 1, FACTORS_NUMBER - 1):
                    for factor_index4 in range(factor_index3 + 1, FACTORS_NUMBER):
                        for factor_index5 in range(factor_index4 + 1, FACTORS_NUMBER + 1):
                            xs_column_names[cur_factors_mult_index] = f'x{factor_index1}x{factor_index2}' \
                                                                      f'x{factor_index3}x{factor_index4}' \
                                                                      f'x{factor_index5}'
                            natural_matrix[:, cur_factors_mult_index] = (
                                    natural_matrix[:, factor_index1] * natural_matrix[:, factor_index2] *
                                    natural_matrix[:, factor_index3] * natural_matrix[:, factor_index4] *
                                    natural_matrix[:, factor_index5])
                            norm_matrix[:, cur_factors_mult_index] = (
                                    norm_matrix[:, factor_index1] * norm_matrix[:, factor_index2] *
                                    norm_matrix[:, factor_index3] * norm_matrix[:, factor_index4] *
                                    norm_matrix[:, factor_index5])
                            cur_factors_mult_index += 1

        assert cur_factors_mult_index == M_SIZE - 1
        xs_column_names[cur_factors_mult_index] = 'x1x2x3x4x5x6'
        natural_matrix[:, cur_factors_mult_index] = (
                natural_matrix[:, 1] * natural_matrix[:, 2] * natural_matrix[:, 3] *
                natural_matrix[:, 4] * natural_matrix[:, 5] * natural_matrix[:, 6])
        norm_matrix[:, cur_factors_mult_index] = (
                norm_matrix[:, 1] * norm_matrix[:, 2] * norm_matrix[:, 3] *
                norm_matrix[:, 4] * norm_matrix[:, 5] * norm_matrix[:, 6])

        self.PFE_natural_matrix = natural_matrix
        self.PFE_norm_matrix = norm_matrix
        self.PFE_column_names = xs_column_names

    def create_DFE4_plan_matrix(self):
        # P=2, n=2^(k-p)=2^(6-2)=2^4=16 опытов
        # Генерирующие соотношения
        #   x5=x1x2x3x4
        #   x6=x1x2x3
        # 22
        xs_column_names = ['x0', 'x1', 'x2', 'x3', 'x4=x5x6',  # 0-4
                           'x1x2=x3x6', 'x1x3=x1x6=x2x6', 'x1x4', 'x2x3', 'x2x4', 'x3x4',  # 5-10
                           'x1x2x3=x6=x4x5', 'x1x2x4=x3x5', 'x1x3x4=x2x5', 'x2x3x4=x1x5',  # 11-14
                           'x1x2x3x4=x5=x4x6']  # 15
        # x0, x1, x2, x3, x4, x5, x6,
        # x1x2, x1x3, x1x4, x1x5, x1x6,
        # x2x3, x2x4, x2x5, x2x6,
        # x3x4, x3x5, x3x6
        # x4x5, x4x6, x5x6
        self.DFE4_map_coefficients = [
            0, 1, 2, 3, 4, 15, 11,
            5, 6, 7, 14, 6,
            8, 9, 13, 6,
            10, 12, 5,
            11, 15, 4
        ]

        # fill everything with minimums
        natural_row = ([1] +  # x0
                       [self.min_maxes_nat[factor_index][0] for factor_index in range(FACTORS_NUMBER_D4)] +
                       [1] * (M_SIZE_D4 - FACTORS_NUMBER_D4 - 1))  # temporary (just to give space)
        natural_matrix = np.array([natural_row for _ in range(M_SIZE_D4)])
        norm_row = ([1] +  # x0
                    [self.min_maxes_norm[factor_index][0] for factor_index in range(FACTORS_NUMBER_D4)] +
                    [1] * (M_SIZE_D4 - FACTORS_NUMBER_D4 - 1))  # temporary (just to give space)
        norm_matrix = np.array([norm_row for _ in range(M_SIZE_D4)])

        for factor_index in range(1, FACTORS_NUMBER_D4 + 1):
            period = pow(2, FACTORS_NUMBER_D4 - factor_index)
            for start_minus in range(period, M_SIZE_D4, 2 * period):
                for row_number in range(start_minus, start_minus + period):
                    natural_matrix[row_number, factor_index] = self.min_maxes_nat[factor_index - 1][1]  # add maxes
                    norm_matrix[row_number, factor_index] = self.min_maxes_norm[factor_index - 1][1]

        # 2
        cur_factors_mult_index = 5
        for factor_index1 in range(1, FACTORS_NUMBER_D4):
            for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER_D4 + 1):
                natural_matrix[:, cur_factors_mult_index] = natural_matrix[:, factor_index1] * natural_matrix[:,
                                                                                               factor_index2]
                norm_matrix[:, cur_factors_mult_index] = norm_matrix[:, factor_index1] * norm_matrix[:, factor_index2]
                cur_factors_mult_index += 1

        # 3
        for factor_index1 in range(1, FACTORS_NUMBER_D4 - 1):
            for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER_D4):
                for factor_index3 in range(factor_index2 + 1, FACTORS_NUMBER_D4 + 1):
                    natural_matrix[:, cur_factors_mult_index] = (
                            natural_matrix[:, factor_index1] * natural_matrix[:, factor_index2] *
                            natural_matrix[:, factor_index3])
                    norm_matrix[:, cur_factors_mult_index] = (
                            norm_matrix[:, factor_index1] * norm_matrix[:, factor_index2] *
                            norm_matrix[:, factor_index3])
                    cur_factors_mult_index += 1

        assert cur_factors_mult_index == M_SIZE_D4 - 1
        natural_matrix[:, cur_factors_mult_index] = (natural_matrix[:, 1] * natural_matrix[:, 2] *
                                                     natural_matrix[:, 3] * natural_matrix[:, 4])
        norm_matrix[:, cur_factors_mult_index] = (norm_matrix[:, 1] * norm_matrix[:, 2] * norm_matrix[:, 3] *
                                                  norm_matrix[:, 4])
        # 16
        self.DFE4_natural_matrix = natural_matrix
        self.DFE4_norm_matrix = norm_matrix
        self.DFE4_column_names = xs_column_names

        # 22
        self.DFE4_natural_matrix_AAA = np.array([np.array(natural_matrix)[:,
                                                 self.DFE4_map_coefficients[i]] for i in
                                                 range(len(self.DFE4_map_coefficients))]).transpose()

        self.DFE4_norm_matrix_AAA = np.array([np.array(norm_matrix)[:,
                                              self.DFE4_map_coefficients[i]] for i in
                                              range(len(self.DFE4_map_coefficients))]).transpose()

        self.DFE4_column_names_AAA = ['x0', 'x1', 'x2', 'x3', 'x4', 'x5', 'x6',
                                      'x1x2', 'x1x3', 'x1x4', 'x1x5', 'x1x6', 'x2x3', 'x2x4', 'x2x5', 'x2x6',
                                      'x3x4', 'x3x5', 'x3x6', 'x4x5', 'x4x6', 'x5x6']

    def create_DFE2_plan_matrix(self):
        # P=1, n=2^(k-p)=2^(6-1)=2^5=32 опыта
        # Генерирующее соотношение
        #   x6=x1x2x3x4x5
        # 22
        xs_column_names = ['x0', 'x1', 'x2', 'x3', 'x4', 'x5',  # 0-5

                           'x1x2', 'x1x3', 'x1x4', 'x1x5',  # 6-15
                           'x2x3', 'x2x4', 'x2x5',
                           'x3x4', 'x3x5', 'x4x5',

                           'x1x2x3', 'x1x2x4', 'x1x2x5',  # 16-25
                           'x1x3x4', 'x1x3x5', 'x1x3x4',
                           'x2x3x4', 'x2x3x5',
                           'x2x4x5',
                           'x3x4x5',

                           'x1x2x3x4', 'x1x2x3x5', 'x1x2x4x5', 'x1x3x4x5', 'x2x3x4x5',  # 26-30
                           'x1x2x3x4x5']  # 31

        # x0, x1, x2, x3, x4, x5, x6,
        # x1x2, x1x3, x1x4, x1x5, x1x6,
        # x2x3, x2x4, x2x5, x2x6,
        # x3x4, x3x5, x3x6
        # x4x5, x4x6, x5x6
        self.DFE2_map_coefficients = [
            0, 1, 2, 3, 4, 5, 31,
            6, 7, 8, 9, 30,
            10, 11, 12, 29,
            13, 14, 28,
            15, 27, 26
        ]

        # fill everything with minimums
        natural_row = ([1] +  # x0
                       [self.min_maxes_nat[factor_index][0] for factor_index in range(FACTORS_NUMBER_D2)] +
                       [1] * (M_SIZE_D2 - FACTORS_NUMBER_D2 - 1))  # temporary (just to give space)
        natural_matrix = np.array([natural_row for _ in range(M_SIZE_D2)])
        norm_row = ([1] +  # x0
                    [self.min_maxes_norm[factor_index][0] for factor_index in range(FACTORS_NUMBER_D2)] +
                    [1] * (M_SIZE_D2 - FACTORS_NUMBER_D2 - 1))  # temporary (just to give space)
        norm_matrix = np.array([norm_row for _ in range(M_SIZE_D2)])

        for factor_index in range(1, FACTORS_NUMBER_D2 + 1):
            period = pow(2, FACTORS_NUMBER_D2 - factor_index)
            for start_minus in range(period, M_SIZE_D2, 2 * period):
                for row_number in range(start_minus, start_minus + period):
                    natural_matrix[row_number, factor_index] = self.min_maxes_nat[factor_index - 1][1]  # add maxes
                    norm_matrix[row_number, factor_index] = self.min_maxes_norm[factor_index - 1][1]

        # 2
        cur_factors_mult_index = 6
        for factor_index1 in range(1, FACTORS_NUMBER_D2):
            for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER_D2 + 1):
                natural_matrix[:, cur_factors_mult_index] = natural_matrix[:, factor_index1] * natural_matrix[:,
                                                                                               factor_index2]
                norm_matrix[:, cur_factors_mult_index] = norm_matrix[:, factor_index1] * norm_matrix[:, factor_index2]
                cur_factors_mult_index += 1

        # 3
        for factor_index1 in range(1, FACTORS_NUMBER_D2 - 1):
            for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER_D2):
                for factor_index3 in range(factor_index2 + 1, FACTORS_NUMBER_D2 + 1):
                    natural_matrix[:, cur_factors_mult_index] = (
                            natural_matrix[:, factor_index1] * natural_matrix[:, factor_index2] *
                            natural_matrix[:, factor_index3])
                    norm_matrix[:, cur_factors_mult_index] = (
                            norm_matrix[:, factor_index1] * norm_matrix[:, factor_index2] *
                            norm_matrix[:, factor_index3])
                    cur_factors_mult_index += 1

        # 4
        for factor_index1 in range(1, FACTORS_NUMBER_D2 - 2):
            for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER_D2 - 1):
                for factor_index3 in range(factor_index2 + 1, FACTORS_NUMBER_D2):
                    for factor_index4 in range(factor_index3 + 1, FACTORS_NUMBER_D2 + 1):
                        natural_matrix[:, cur_factors_mult_index] = (
                                natural_matrix[:, factor_index1] * natural_matrix[:, factor_index2] *
                                natural_matrix[:, factor_index3] * natural_matrix[:, factor_index4])
                        norm_matrix[:, cur_factors_mult_index] = (
                                norm_matrix[:, factor_index1] * norm_matrix[:, factor_index2] *
                                norm_matrix[:, factor_index3] * norm_matrix[:, factor_index4])
                        cur_factors_mult_index += 1

        assert cur_factors_mult_index == M_SIZE_D2 - 1
        natural_matrix[:, cur_factors_mult_index] = (natural_matrix[:, 1] * natural_matrix[:, 2] *
                                                     natural_matrix[:, 3] * natural_matrix[:, 4] *
                                                     natural_matrix[:, 5])
        norm_matrix[:, cur_factors_mult_index] = (norm_matrix[:, 1] * norm_matrix[:, 2] * norm_matrix[:, 3] *
                                                  norm_matrix[:, 4] * norm_matrix[:, 5])
        # 16
        self.DFE2_natural_matrix = natural_matrix
        self.DFE2_norm_matrix = norm_matrix
        self.DFE2_column_names = xs_column_names

        # 22
        self.DFE2_natural_matrix_AAA = np.array([np.array(natural_matrix)[:,
                                                 self.DFE2_map_coefficients[i]] for i in
                                                 range(len(self.DFE2_map_coefficients))]).transpose()

        self.DFE2_norm_matrix_AAA = np.array([np.array(norm_matrix)[:,
                                              self.DFE2_map_coefficients[i]] for i in
                                              range(len(self.DFE2_map_coefficients))]).transpose()

        self.DFE2_column_names_AAA = ['x0', 'x1', 'x2', 'x3', 'x4', 'x5', 'x6',
                                      'x1x2', 'x1x3', 'x1x4', 'x1x5', 'x1x6', 'x2x3', 'x2x4', 'x2x5', 'x2x6',
                                      'x3x4', 'x3x5', 'x3x6', 'x4x5', 'x4x6', 'x5x6']

    def process_results_PFE(self, experiment_results: np.array):
        # b = [X^T * X]^-1  * X^T * y_exp
        x = self.PFE_norm_matrix
        norm_coefficients = np.dot(np.dot(np.linalg.inv(np.dot(np.transpose(x), x)), np.transpose(x)),
                                   experiment_results)

        x = self.PFE_natural_matrix
        nat_coefficients = np.dot(np.dot(np.linalg.inv(np.dot(np.transpose(x), x)), np.transpose(x)),
                                  experiment_results)
        real_nat_coefficients = self.norm_to_natural_coefficients(norm_coefficients, FACTORS_NUMBER)

        norm_nonlinear_approximations = [
            sum(self.PFE_norm_matrix[i, :] * norm_coefficients[:])
            for i in range(M_SIZE)]
        norm_linear_approximations = [
            sum(self.PFE_norm_matrix[i, :LIN_COEFS_AMOUNT] * norm_coefficients[:LIN_COEFS_AMOUNT])
            for i in range(M_SIZE)]

        nat_nonlinear_approximations = [
            sum(self.PFE_natural_matrix[i, :] * nat_coefficients[:])
            for i in range(M_SIZE)]

        real_nat_nonlinear_approximations = [
            sum(self.PFE_natural_matrix[i, :len(real_nat_coefficients)] * real_nat_coefficients[:])
            for i in range(M_SIZE)]

        nat_linear_approximations = [
            sum(self.PFE_natural_matrix[i, :LIN_COEFS_AMOUNT] * nat_coefficients[:LIN_COEFS_AMOUNT])
            for i in range(M_SIZE)]

        real_nat_linear_approximations = [
            sum(self.PFE_natural_matrix[i, :LIN_COEFS_AMOUNT] * real_nat_coefficients[:LIN_COEFS_AMOUNT])
            for i in range(M_SIZE)]

        # concatenate
        norm_full_results = np.c_[self.PFE_norm_matrix,
                                  experiment_results, norm_linear_approximations, norm_nonlinear_approximations,
                                  np.abs(experiment_results - norm_linear_approximations),
                                  np.abs(experiment_results - norm_nonlinear_approximations)]

        nat_full_results = np.c_[self.PFE_natural_matrix,
                                 experiment_results, nat_linear_approximations, nat_nonlinear_approximations,
                                 np.abs(experiment_results - nat_linear_approximations),
                                 np.abs(experiment_results - nat_nonlinear_approximations)]

        real_nat_full_results = np.c_[self.PFE_natural_matrix,
                                      experiment_results, real_nat_linear_approximations, real_nat_nonlinear_approximations,
                                      np.abs(experiment_results - real_nat_linear_approximations),
                                      np.abs(experiment_results - real_nat_nonlinear_approximations)]

        self.norm_full_results_table_PFE = norm_full_results
        self.norm_coefficients_PFE = norm_coefficients

        self.nat_full_results_table_PFE = nat_full_results
        self.nat_coefficients_PFE = nat_coefficients

        self.real_nat_full_results_table_PFE = real_nat_full_results
        self.real_nat_coefficients_PFE = real_nat_coefficients

        self.PFE_column_names += ['y', 'y_l', 'y_nl', '|y-yl|', '|y-ynl|']

    def process_results_DFE4(self, experiment_results: np.array):
        # b = [X^T * X]^-1  * X^T * y_exp
        x = self.DFE4_norm_matrix
        norm_coefficients = np.dot(np.dot(np.linalg.inv(np.dot(np.transpose(x), x)), np.transpose(x)),
                                   experiment_results)

        x = self.DFE4_natural_matrix
        nat_coefficients = np.dot(np.dot(np.linalg.inv(np.dot(np.transpose(x), x)), np.transpose(x)),
                                  experiment_results)
        real_nat_coefficients = self.norm_to_natural_coefficients(norm_coefficients, FACTORS_NUMBER_D4)

        norm_nonlinear_approximations = [
            sum(self.DFE4_norm_matrix[i, :] * norm_coefficients[:])
            for i in range(M_SIZE_D4)]
        norm_linear_approximations = [
            sum(self.DFE4_norm_matrix[i, :LIN_COEFS_AMOUNT_D4] * norm_coefficients[:LIN_COEFS_AMOUNT_D4])
            for i in range(M_SIZE_D4)]

        nat_nonlinear_approximations = [
            sum(self.DFE4_natural_matrix[i, :] * nat_coefficients[:])
            for i in range(M_SIZE_D4)]
        nat_linear_approximations = [
            sum(self.DFE4_natural_matrix[i, :LIN_COEFS_AMOUNT_D4] * nat_coefficients[:LIN_COEFS_AMOUNT_D4])
            for i in range(M_SIZE_D4)]

        real_nat_nonlinear_approximations = [
            sum(self.DFE4_natural_matrix[i, :len(real_nat_coefficients)] * real_nat_coefficients[:])
            for i in range(M_SIZE_D4)]
        real_nat_linear_approximations = [
            sum(self.DFE4_natural_matrix[i, :LIN_COEFS_AMOUNT_D4] * real_nat_coefficients[:LIN_COEFS_AMOUNT_D4])
            for i in range(M_SIZE_D4)]

        # concatenate
        norm_full_results = np.c_[self.DFE4_norm_matrix,
                                  experiment_results, norm_linear_approximations, norm_nonlinear_approximations,
                                  np.abs(experiment_results - norm_linear_approximations),
                                  np.abs(experiment_results - norm_nonlinear_approximations)]

        norm_full_results_AAA = np.c_[self.DFE4_norm_matrix_AAA,
                                      experiment_results, norm_linear_approximations, norm_nonlinear_approximations,
                                      np.abs(experiment_results - norm_linear_approximations),
                                      np.abs(experiment_results - norm_nonlinear_approximations)]

        nat_full_results = np.c_[self.DFE4_natural_matrix,
                                 experiment_results, nat_linear_approximations, nat_nonlinear_approximations,
                                 np.abs(experiment_results - nat_linear_approximations),
                                 np.abs(experiment_results - nat_nonlinear_approximations)]

        nat_full_results_AAA = np.c_[self.DFE4_natural_matrix_AAA,
                                     experiment_results, nat_linear_approximations, nat_nonlinear_approximations,
                                     np.abs(experiment_results - nat_linear_approximations),
                                     np.abs(experiment_results - nat_nonlinear_approximations)]

        real_nat_full_results = np.c_[self.DFE4_natural_matrix,
                                 experiment_results, real_nat_linear_approximations, real_nat_nonlinear_approximations,
                                 np.abs(experiment_results - real_nat_linear_approximations),
                                 np.abs(experiment_results - real_nat_nonlinear_approximations)]

        real_nat_full_results_AAA = np.c_[self.DFE4_natural_matrix_AAA,
                                     experiment_results, real_nat_linear_approximations, real_nat_nonlinear_approximations,
                                     np.abs(experiment_results - real_nat_linear_approximations),
                                     np.abs(experiment_results - real_nat_nonlinear_approximations)]

        self.norm_full_results_table_DFE4 = norm_full_results
        self.norm_coefficients_DFE4 = norm_coefficients

        self.nat_full_results_table_DFE4 = nat_full_results
        self.nat_coefficients_DFE4 = nat_coefficients
        self.real_nat_full_results_table_DFE4 = real_nat_full_results
        self.real_nat_coefficients_DFE4 = real_nat_coefficients

        self.norm_full_results_table_DFE4_AAA = norm_full_results_AAA
        self.norm_coefficients_DFE4_AAA = [norm_coefficients[
                                               self.DFE4_map_coefficients[i]] for i in
                                           range(len(self.DFE4_map_coefficients))]
        self.nat_full_results_table_DFE4_AAA = nat_full_results_AAA
        self.nat_coefficients_DFE4_AAA = [nat_coefficients[
                                              self.DFE4_map_coefficients[i]] for i in
                                          range(len(self.DFE4_map_coefficients))]
        self.real_nat_full_results_table_DFE4_AAA = real_nat_full_results_AAA
        self.real_nat_coefficients_DFE4_AAA = [real_nat_coefficients[
                                              self.DFE4_map_coefficients[i]] for i in
                                          range(len(self.DFE4_map_coefficients))]

        self.DFE4_column_names += ['y', 'y_l', 'y_nl', '|y-yl|', '|y-ynl|']
        self.DFE4_column_names_AAA += ['y', 'y_l', 'y_nl', '|y-yl|', '|y-ynl|']

    def process_results_DFE2(self, experiment_results: np.array):
        # b = [X^T * X]^-1  * X^T * y_exp
        x = self.DFE2_norm_matrix
        norm_coefficients = np.dot(np.dot(np.linalg.inv(np.dot(np.transpose(x), x)), np.transpose(x)),
                                   experiment_results)

        x = self.DFE2_natural_matrix
        nat_coefficients = np.dot(np.dot(np.linalg.inv(np.dot(np.transpose(x), x)), np.transpose(x)),
                                  experiment_results)
        real_nat_coefficients = self.norm_to_natural_coefficients(norm_coefficients, FACTORS_NUMBER_D2)

        norm_nonlinear_approximations = [
            sum(self.DFE2_norm_matrix[i, :] * norm_coefficients[:])
            for i in range(M_SIZE_D2)]
        norm_linear_approximations = [
            sum(self.DFE2_norm_matrix[i, :LIN_COEFS_AMOUNT_D2] * norm_coefficients[:LIN_COEFS_AMOUNT_D2])
            for i in range(M_SIZE_D2)]

        nat_nonlinear_approximations = [
            sum(self.DFE2_natural_matrix[i, :] * nat_coefficients[:])
            for i in range(M_SIZE_D2)]
        nat_linear_approximations = [
            sum(self.DFE2_natural_matrix[i, :LIN_COEFS_AMOUNT_D2] * nat_coefficients[:LIN_COEFS_AMOUNT_D2])
            for i in range(M_SIZE_D2)]

        real_nat_nonlinear_approximations = [
            sum(self.DFE2_natural_matrix[i, :len(real_nat_coefficients)] * real_nat_coefficients[:])
            for i in range(M_SIZE_D2)]
        real_nat_linear_approximations = [
            sum(self.DFE2_natural_matrix[i, :LIN_COEFS_AMOUNT_D2] * real_nat_coefficients[:LIN_COEFS_AMOUNT_D2])
            for i in range(M_SIZE_D2)]

        # concatenate
        norm_full_results = np.c_[self.DFE2_norm_matrix,
                                  experiment_results, norm_linear_approximations, norm_nonlinear_approximations,
                                  np.abs(experiment_results - norm_linear_approximations),
                                  np.abs(experiment_results - norm_nonlinear_approximations)]

        norm_full_results_AAA = np.c_[self.DFE2_norm_matrix_AAA,
                                      experiment_results, norm_linear_approximations, norm_nonlinear_approximations,
                                      np.abs(experiment_results - norm_linear_approximations),
                                      np.abs(experiment_results - norm_nonlinear_approximations)]

        nat_full_results = np.c_[self.DFE2_natural_matrix,
                                 experiment_results, nat_linear_approximations, nat_nonlinear_approximations,
                                 np.abs(experiment_results - nat_linear_approximations),
                                 np.abs(experiment_results - nat_nonlinear_approximations)]

        nat_full_results_AAA = np.c_[self.DFE2_natural_matrix_AAA,
                                     experiment_results, nat_linear_approximations, nat_nonlinear_approximations,
                                     np.abs(experiment_results - nat_linear_approximations),
                                     np.abs(experiment_results - nat_nonlinear_approximations)]

        real_nat_full_results = np.c_[self.DFE2_natural_matrix,
                                 experiment_results, real_nat_linear_approximations, real_nat_nonlinear_approximations,
                                 np.abs(experiment_results - real_nat_linear_approximations),
                                 np.abs(experiment_results - real_nat_nonlinear_approximations)]

        real_nat_full_results_AAA = np.c_[self.DFE2_natural_matrix_AAA,
                                     experiment_results, real_nat_linear_approximations, real_nat_nonlinear_approximations,
                                     np.abs(experiment_results - real_nat_linear_approximations),
                                     np.abs(experiment_results - real_nat_nonlinear_approximations)]

        self.norm_full_results_table_DFE2 = norm_full_results
        self.norm_coefficients_DFE2 = norm_coefficients

        self.nat_full_results_table_DFE2 = nat_full_results
        self.nat_coefficients_DFE2 = nat_coefficients
        self.real_nat_full_results_table_DFE2 = real_nat_full_results
        self.real_nat_coefficients_DFE2 = real_nat_coefficients

        self.norm_full_results_table_DFE2_AAA = norm_full_results_AAA
        self.norm_coefficients_DFE2_AAA = [norm_coefficients[
                                               self.DFE2_map_coefficients[i]] for i in
                                           range(len(self.DFE2_map_coefficients))]
        self.nat_full_results_table_DFE2_AAA = nat_full_results_AAA
        self.nat_coefficients_DFE2_AAA = [nat_coefficients[
                                              self.DFE2_map_coefficients[i]] for i in
                                          range(len(self.DFE2_map_coefficients))]
        self.real_nat_full_results_table_DFE2_AAA = real_nat_full_results_AAA
        self.real_nat_coefficients_DFE2_AAA = [real_nat_coefficients[
                                              self.DFE2_map_coefficients[i]] for i in
                                          range(len(self.DFE2_map_coefficients))]

        self.DFE2_column_names += ['y', 'y_l', 'y_nl', '|y-yl|', '|y-ynl|']
        self.DFE2_column_names_AAA += ['y', 'y_l', 'y_nl', '|y-yl|', '|y-ynl|']

    def run_PFE(self):
        # print(plan_matrix_normalized)
        experiment_results = np.zeros(M_SIZE)

        for exp_number, exp_params in enumerate(self.PFE_norm_matrix):
            gen_int = self.nat_factor_from_norm(exp_params[1], self.global_gen_int_min, self.global_gen_int_max)
            proc_int = self.nat_factor_from_norm(exp_params[2], self.global_proc_int_min, self.global_proc_int_max)
            proc_var = self.nat_factor_from_norm(exp_params[3], self.global_proc_var_min, self.global_proc_var_max)
            gen_int2 = self.nat_factor_from_norm(exp_params[4], self.global_gen_int_min, self.global_gen_int_max)
            proc_int2 = self.nat_factor_from_norm(exp_params[5], self.global_proc_int_min, self.global_proc_int_max)
            proc_var2 = self.nat_factor_from_norm(exp_params[6], self.global_proc_var_min, self.global_proc_var_max)

            lambda_, mu, sigma = self.convert_params(gen_int, proc_int, proc_var)
            lambda_2, mu2, sigma2 = self.convert_params(gen_int2, proc_int2, proc_var2)

            cur_experiment_results = []
            for _ in range(N_REPEATS):
                generators = [Generator(distributions.ExponentialDistribution(lambda_)),
                              Generator(distributions.ExponentialDistribution(lambda_2))]
                processor = Processor([distributions.NormalDistribution(mu, sigma),
                                       distributions.NormalDistribution(mu2, sigma2)])
                modeller = Modeller(generators, processor)
                modelling_results = modeller.event_modelling(self.requests_amount)
                cur_experiment_results.append(modelling_results['mean_time_in_queue'])

            experiment_results[exp_number] = sum(cur_experiment_results) / N_REPEATS

        self.process_results_PFE(experiment_results)

    def run_DFE4(self):
        # print(plan_matrix_normalized)
        experiment_results = np.zeros(M_SIZE_D4)

        for exp_number, exp_params in enumerate(self.DFE4_norm_matrix):
            gen_int = self.nat_factor_from_norm(exp_params[1], self.global_gen_int_min, self.global_gen_int_max)
            proc_int = self.nat_factor_from_norm(exp_params[2], self.global_proc_int_min, self.global_proc_int_max)
            proc_var = self.nat_factor_from_norm(exp_params[3], self.global_proc_var_min, self.global_proc_var_max)
            gen_int2 = self.nat_factor_from_norm(exp_params[4], self.global_gen_int_min, self.global_gen_int_max)
            proc_int2 = self.nat_factor_from_norm(exp_params[self.DFE4_map_coefficients[5]], self.global_proc_int_min,
                                                  self.global_proc_int_max)
            proc_var2 = self.nat_factor_from_norm(exp_params[self.DFE4_map_coefficients[6]], self.global_proc_var_min,
                                                  self.global_proc_var_max)

            lambda_, mu, sigma = self.convert_params(gen_int, proc_int, proc_var)
            lambda_2, mu2, sigma2 = self.convert_params(gen_int2, proc_int2, proc_var2)

            cur_experiment_results = []
            for _ in range(N_REPEATS):
                generators = [Generator(distributions.ExponentialDistribution(lambda_)),
                              Generator(distributions.ExponentialDistribution(lambda_2))]
                processor = Processor([distributions.NormalDistribution(mu, sigma),
                                       distributions.NormalDistribution(mu2, sigma2)])
                modeller = Modeller(generators, processor)
                modelling_results = modeller.event_modelling(self.requests_amount)
                cur_experiment_results.append(modelling_results['mean_time_in_queue'])

            experiment_results[exp_number] = sum(cur_experiment_results) / N_REPEATS

        self.process_results_DFE4(experiment_results)

    def run_DFE2(self):
        # print(plan_matrix_normalized)
        experiment_results = np.zeros(M_SIZE_D2)

        for exp_number, exp_params in enumerate(self.DFE2_norm_matrix):
            gen_int = self.nat_factor_from_norm(exp_params[1], self.global_gen_int_min, self.global_gen_int_max)
            proc_int = self.nat_factor_from_norm(exp_params[2], self.global_proc_int_min, self.global_proc_int_max)
            proc_var = self.nat_factor_from_norm(exp_params[3], self.global_proc_var_min, self.global_proc_var_max)
            gen_int2 = self.nat_factor_from_norm(exp_params[4], self.global_gen_int_min, self.global_gen_int_max)
            proc_int2 = self.nat_factor_from_norm(exp_params[5], self.global_proc_int_min, self.global_proc_int_max)
            proc_var2 = self.nat_factor_from_norm(exp_params[self.DFE4_map_coefficients[6]], self.global_proc_var_min,
                                                  self.global_proc_var_max)

            lambda_, mu, sigma = self.convert_params(gen_int, proc_int, proc_var)
            lambda_2, mu2, sigma2 = self.convert_params(gen_int2, proc_int2, proc_var2)

            cur_experiment_results = []
            for _ in range(N_REPEATS):
                generators = [Generator(distributions.ExponentialDistribution(lambda_)),
                              Generator(distributions.ExponentialDistribution(lambda_2))]
                processor = Processor([distributions.NormalDistribution(mu, sigma),
                                       distributions.NormalDistribution(mu2, sigma2)])
                modeller = Modeller(generators, processor)
                modelling_results = modeller.event_modelling(self.requests_amount)
                cur_experiment_results.append(modelling_results['mean_time_in_queue'])

            experiment_results[exp_number] = sum(cur_experiment_results) / N_REPEATS

        self.process_results_DFE2(experiment_results)

    def check(self,
              gen_int_normalized, proc_int_normalized, proc_var_normalized,
              gen_int_normalized2, proc_int_normalized2, proc_var_normalized2, is_natural):

        if not is_natural:
            gen_int_nat = self.nat_factor_from_norm(gen_int_normalized, self.global_gen_int_min,
                                                    self.global_gen_int_max)
            proc_int_nat = self.nat_factor_from_norm(proc_int_normalized, self.global_proc_int_min,
                                                     self.global_proc_int_max)
            proc_var_nat = self.nat_factor_from_norm(proc_var_normalized, self.global_proc_var_min,
                                                     self.global_proc_var_max)
            gen_int2_nat = self.nat_factor_from_norm(gen_int_normalized2, self.global_gen_int_min,
                                                     self.global_gen_int_max)
            proc_int2_nat = self.nat_factor_from_norm(proc_int_normalized2, self.global_proc_int_min,
                                                      self.global_proc_int_max)
            proc_var2_nat = self.nat_factor_from_norm(proc_var_normalized2, self.global_proc_var_min,
                                                      self.global_proc_var_max)
        else:
            gen_int_nat = gen_int_normalized
            proc_int_nat = proc_int_normalized
            proc_var_nat = proc_var_normalized
            gen_int2_nat = gen_int_normalized2
            proc_int2_nat = proc_int_normalized2
            proc_var2_nat = proc_var_normalized2

            gen_int_normalized = self.norm_factor_from_nat(gen_int_normalized, self.global_gen_int_min,
                                                           self.global_gen_int_max)
            proc_int_normalized = self.norm_factor_from_nat(proc_int_normalized, self.global_proc_int_min,
                                                            self.global_proc_int_max)
            proc_var_normalized = self.norm_factor_from_nat(proc_var_normalized, self.global_proc_var_min,
                                                            self.global_proc_var_max)
            gen_int_normalized2 = self.norm_factor_from_nat(gen_int_normalized2, self.global_gen_int_min,
                                                            self.global_gen_int_max)
            proc_int_normalized2 = self.norm_factor_from_nat(proc_int_normalized2, self.global_proc_int_min,
                                                             self.global_proc_int_max)
            proc_var_normalized2 = self.norm_factor_from_nat(proc_var_normalized2, self.global_proc_var_min,
                                                             self.global_proc_var_max)

        lambda_, mu, sigma = self.convert_params(gen_int_nat, proc_int_nat, proc_var_nat)
        lambda_2, mu2, sigma2 = self.convert_params(gen_int2_nat, proc_int2_nat, proc_var2_nat)

        cur_experiment_results = []
        for _ in range(N_REPEATS):
            generators = [Generator(distributions.ExponentialDistribution(lambda_)),
                          Generator(distributions.ExponentialDistribution(lambda_2))]
            processor = Processor([distributions.NormalDistribution(mu, sigma),
                                   distributions.NormalDistribution(mu2, sigma2)])
            modeller = Modeller(generators, processor)
            modelling_results = modeller.event_modelling(self.requests_amount)
            cur_experiment_results.append(modelling_results['mean_time_in_queue'])

        experiment_result = sum(cur_experiment_results) / N_REPEATS

        experiment_plan_row_norm_PFE = np.array(
            [1] +
            [gen_int_normalized, proc_int_normalized, proc_var_normalized, gen_int_normalized2, proc_int_normalized2,
             proc_var_normalized2, ] +
            [1] * (M_SIZE - FACTORS_NUMBER - 1)

        )
        experiment_plan_row_nat_PFE = np.array(
            [1] +
            [gen_int_nat, proc_int_nat, proc_var_nat, gen_int2_nat, proc_int2_nat,
             proc_var2_nat, ] +
            [1] * (M_SIZE - FACTORS_NUMBER - 1)
        )

        # 2
        cur_factors_mult_index = 7
        for factor_index1 in range(1, FACTORS_NUMBER):
            for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER + 1):
                experiment_plan_row_norm_PFE[cur_factors_mult_index] = (experiment_plan_row_norm_PFE[factor_index1] *
                                                                        experiment_plan_row_norm_PFE[factor_index2])
                experiment_plan_row_nat_PFE[cur_factors_mult_index] = (experiment_plan_row_nat_PFE[factor_index1] *
                                                                       experiment_plan_row_nat_PFE[factor_index2])
                cur_factors_mult_index += 1

        # 3
        for factor_index1 in range(1, FACTORS_NUMBER - 1):
            for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER):
                for factor_index3 in range(factor_index2 + 1, FACTORS_NUMBER + 1):
                    experiment_plan_row_norm_PFE[cur_factors_mult_index] = (
                            experiment_plan_row_norm_PFE[factor_index1] *
                            experiment_plan_row_norm_PFE[factor_index2] *
                            experiment_plan_row_norm_PFE[factor_index3])
                    experiment_plan_row_nat_PFE[cur_factors_mult_index] = (
                            experiment_plan_row_nat_PFE[factor_index1] *
                            experiment_plan_row_nat_PFE[factor_index2] *
                            experiment_plan_row_nat_PFE[factor_index3])
                    cur_factors_mult_index += 1

        # 4
        for factor_index1 in range(1, FACTORS_NUMBER - 2):
            for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER - 1):
                for factor_index3 in range(factor_index2 + 1, FACTORS_NUMBER):
                    for factor_index4 in range(factor_index3 + 1, FACTORS_NUMBER + 1):
                        experiment_plan_row_norm_PFE[cur_factors_mult_index] = (
                                experiment_plan_row_norm_PFE[factor_index1] *
                                experiment_plan_row_norm_PFE[factor_index2] *
                                experiment_plan_row_norm_PFE[factor_index3] *
                                experiment_plan_row_norm_PFE[factor_index4])
                        experiment_plan_row_nat_PFE[cur_factors_mult_index] = (
                                experiment_plan_row_nat_PFE[factor_index1] *
                                experiment_plan_row_nat_PFE[factor_index2] *
                                experiment_plan_row_nat_PFE[factor_index3] *
                                experiment_plan_row_nat_PFE[factor_index4])
                        cur_factors_mult_index += 1

        # 5
        for factor_index1 in range(1, FACTORS_NUMBER - 3):
            for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER - 2):
                for factor_index3 in range(factor_index2 + 1, FACTORS_NUMBER - 1):
                    for factor_index4 in range(factor_index3 + 1, FACTORS_NUMBER):
                        for factor_index5 in range(factor_index4 + 1, FACTORS_NUMBER + 1):
                            experiment_plan_row_norm_PFE[cur_factors_mult_index] = (
                                    experiment_plan_row_norm_PFE[factor_index1] *
                                    experiment_plan_row_norm_PFE[factor_index2] *
                                    experiment_plan_row_norm_PFE[factor_index3] *
                                    experiment_plan_row_norm_PFE[factor_index4] *
                                    experiment_plan_row_norm_PFE[factor_index5])
                            experiment_plan_row_nat_PFE[cur_factors_mult_index] = (
                                    experiment_plan_row_nat_PFE[factor_index1] *
                                    experiment_plan_row_nat_PFE[factor_index2] *
                                    experiment_plan_row_nat_PFE[factor_index3] *
                                    experiment_plan_row_nat_PFE[factor_index4] *
                                    experiment_plan_row_nat_PFE[factor_index5])
                            cur_factors_mult_index += 1

        assert cur_factors_mult_index == M_SIZE - 1
        experiment_plan_row_norm_PFE[cur_factors_mult_index] = (
                experiment_plan_row_norm_PFE[1] * experiment_plan_row_norm_PFE[2] *
                experiment_plan_row_norm_PFE[3] * experiment_plan_row_norm_PFE[4] *
                experiment_plan_row_norm_PFE[5] * experiment_plan_row_norm_PFE[6])
        experiment_plan_row_nat_PFE[cur_factors_mult_index] = (
                experiment_plan_row_nat_PFE[1] * experiment_plan_row_nat_PFE[2] *
                experiment_plan_row_nat_PFE[3] * experiment_plan_row_nat_PFE[4] *
                experiment_plan_row_nat_PFE[5] * experiment_plan_row_nat_PFE[6])
        experiment_plan_row_norm_PFE = np.array(experiment_plan_row_norm_PFE)
        experiment_plan_row_nat_PFE = np.array(experiment_plan_row_nat_PFE)

        nonlinear_approximation_norm_PFE = sum(experiment_plan_row_norm_PFE * self.norm_coefficients_PFE)
        nonlinear_approximation_nat_PFE = sum(experiment_plan_row_nat_PFE * self.nat_coefficients_PFE)

        linear_approximation_norm_PFE = sum(
            experiment_plan_row_norm_PFE[:LIN_COEFS_AMOUNT] * self.norm_coefficients_PFE[:LIN_COEFS_AMOUNT])
        linear_approximation_nat_PFE = sum(
            experiment_plan_row_nat_PFE[:LIN_COEFS_AMOUNT] * self.nat_coefficients_PFE[:LIN_COEFS_AMOUNT])

        total_norm_PFE = list(experiment_plan_row_norm_PFE)
        total_nat_PFE = list(experiment_plan_row_nat_PFE)

        total_norm_PFE.extend([
            experiment_result, linear_approximation_norm_PFE, nonlinear_approximation_norm_PFE,
            np.abs(experiment_result - linear_approximation_norm_PFE),
            np.abs(experiment_result - nonlinear_approximation_norm_PFE)])

        total_nat_PFE.extend([
            experiment_result, linear_approximation_nat_PFE, nonlinear_approximation_nat_PFE,
            np.abs(experiment_result - linear_approximation_nat_PFE),
            np.abs(experiment_result - nonlinear_approximation_nat_PFE)])

        self.norm_full_results_table_PFE = np.r_[self.norm_full_results_table_PFE, [total_norm_PFE]]
        self.nat_full_results_table_PFE = np.r_[self.nat_full_results_table_PFE, [total_nat_PFE]]

        experiment_plan_row_norm_DFE4 = np.array(
            [1] +
            [gen_int_normalized, proc_int_normalized, proc_var_normalized, gen_int_normalized2,
             proc_int_normalized2, proc_var_normalized2] +
            [1] * 15

        )
        experiment_plan_row_nat_DFE4 = np.array(
            [1] +
            [gen_int_nat, proc_int_nat, proc_var_nat, gen_int2_nat, proc_int2_nat, proc_var2_nat] +
            [1] * 15
        )

        # 2
        cur_factors_mult_index = FACTORS_NUMBER + 1
        for factor_index1 in range(1, FACTORS_NUMBER):
            for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER + 1):
                experiment_plan_row_norm_DFE4[cur_factors_mult_index] = (experiment_plan_row_norm_DFE4[factor_index1] *
                                                                         experiment_plan_row_norm_DFE4[factor_index2])
                experiment_plan_row_nat_DFE4[cur_factors_mult_index] = (experiment_plan_row_nat_DFE4[factor_index1] *
                                                                        experiment_plan_row_nat_DFE4[factor_index2])
                cur_factors_mult_index += 1

        experiment_plan_row_norm_DFE4 = np.array(experiment_plan_row_norm_DFE4)
        experiment_plan_row_nat_DFE4 = np.array(experiment_plan_row_nat_DFE4)

        nonlinear_approximation_norm_DFE4 = sum(experiment_plan_row_norm_DFE4 * self.norm_coefficients_DFE4_AAA)
        nonlinear_approximation_nat_DFE4 = sum(experiment_plan_row_nat_DFE4 * self.nat_coefficients_DFE4_AAA)

        linear_approximation_norm_DFE4 = sum(
            experiment_plan_row_norm_DFE4[:LIN_COEFS_AMOUNT_D4] * self.norm_coefficients_DFE4_AAA[:LIN_COEFS_AMOUNT_D4])
        linear_approximation_nat_DFE4 = sum(
            experiment_plan_row_nat_DFE4[:LIN_COEFS_AMOUNT_D4] * self.nat_coefficients_DFE4_AAA[:LIN_COEFS_AMOUNT_D4])

        total_norm_DFE4 = list(experiment_plan_row_norm_DFE4)
        total_nat_DFE4 = list(experiment_plan_row_nat_DFE4)

        total_norm_DFE4.extend([
            experiment_result, linear_approximation_norm_DFE4, nonlinear_approximation_norm_DFE4,
            np.abs(experiment_result - linear_approximation_norm_DFE4),
            np.abs(experiment_result - nonlinear_approximation_norm_DFE4)])

        total_nat_DFE4.extend([
            experiment_result, linear_approximation_nat_DFE4, nonlinear_approximation_nat_DFE4,
            np.abs(experiment_result - linear_approximation_nat_DFE4),
            np.abs(experiment_result - nonlinear_approximation_nat_DFE4)])

        # TODO но это я лучше вообще использовать не буду
        # self.norm_full_results_table_DFE4 = np.r_[self.norm_full_results_table_DFE4, [total_norm_DFE4]]
        # self.nat_full_results_table_DFE4 = np.r_[self.nat_full_results_table_DFE4, [total_nat_DFE4]]

        self.norm_full_results_table_DFE4_AAA = np.r_[self.norm_full_results_table_DFE4_AAA, [total_norm_DFE4]]
        self.nat_full_results_table_DFE4_AAA = np.r_[self.nat_full_results_table_DFE4_AAA, [total_nat_DFE4]]

        experiment_plan_row_norm_DFE2 = np.array(
            [1] +
            [gen_int_normalized, proc_int_normalized, proc_var_normalized, gen_int_normalized2,
             proc_int_normalized2, proc_var_normalized2] +
            [1] * 15

        )
        experiment_plan_row_nat_DFE2 = np.array(
            [1] +
            [gen_int_nat, proc_int_nat, proc_var_nat, gen_int2_nat, proc_int2_nat, proc_var2_nat] +
            [1] * 15
        )

        # 2
        cur_factors_mult_index = FACTORS_NUMBER + 1
        for factor_index1 in range(1, FACTORS_NUMBER):
            for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER + 1):
                experiment_plan_row_norm_DFE2[cur_factors_mult_index] = (experiment_plan_row_norm_DFE2[factor_index1] *
                                                                         experiment_plan_row_norm_DFE2[factor_index2])
                experiment_plan_row_nat_DFE2[cur_factors_mult_index] = (experiment_plan_row_nat_DFE2[factor_index1] *
                                                                        experiment_plan_row_nat_DFE2[factor_index2])
                cur_factors_mult_index += 1

        experiment_plan_row_norm_DFE2 = np.array(experiment_plan_row_norm_DFE2)
        experiment_plan_row_nat_DFE2 = np.array(experiment_plan_row_nat_DFE2)

        nonlinear_approximation_norm_DFE2 = sum(experiment_plan_row_norm_DFE2 * self.norm_coefficients_DFE2_AAA)
        nonlinear_approximation_nat_DFE2 = sum(experiment_plan_row_nat_DFE2 * self.nat_coefficients_DFE2_AAA)

        linear_approximation_norm_DFE2 = sum(
            experiment_plan_row_norm_DFE2[:LIN_COEFS_AMOUNT_D2] * self.norm_coefficients_DFE2_AAA[:LIN_COEFS_AMOUNT_D2])
        linear_approximation_nat_DFE2 = sum(
            experiment_plan_row_nat_DFE2[:LIN_COEFS_AMOUNT_D2] * self.nat_coefficients_DFE2_AAA[:LIN_COEFS_AMOUNT_D2])

        total_norm_DFE2 = list(experiment_plan_row_norm_DFE2)
        total_nat_DFE2 = list(experiment_plan_row_nat_DFE2)

        total_norm_DFE2.extend([
            experiment_result, linear_approximation_norm_DFE2, nonlinear_approximation_norm_DFE2,
            np.abs(experiment_result - linear_approximation_norm_DFE2),
            np.abs(experiment_result - nonlinear_approximation_norm_DFE2)])

        total_nat_DFE2.extend([
            experiment_result, linear_approximation_nat_DFE2, nonlinear_approximation_nat_DFE2,
            np.abs(experiment_result - linear_approximation_nat_DFE2),
            np.abs(experiment_result - nonlinear_approximation_nat_DFE2)])

        self.norm_full_results_table_DFE2_AAA = np.r_[self.norm_full_results_table_DFE2_AAA, [total_norm_DFE2]]
        self.nat_full_results_table_DFE2_AAA = np.r_[self.nat_full_results_table_DFE2_AAA, [total_nat_DFE2]]

    def norm_to_natural_coefficients(self, norm_coefficients, n_factors):
        norm_coefficients = list(norm_coefficients)

        x0s = [None, ] + [(self.min_maxes_nat[i][1] + self.min_maxes_nat[i][0]) / 2 for i in range(n_factors)]
        intervals = [None, ] + [(self.min_maxes_nat[i][1] - self.min_maxes_nat[i][0]) / 2 for i in range(n_factors)]

        b0_nat = norm_coefficients.pop(0)

        all_indexes = set(range(1, n_factors + 1))
        all_my_combinations = {by: list(combinations(all_indexes, by)) for by in range(1, 4)}  # комбинации по n индексов

        # заполняем исходные (нормированные) коэффициенты
        b = dict()
        cur_index_in_coefficients = 0
        for by, combinations_by in all_my_combinations.items():
            for combination in combinations_by:
                b[combination] = norm_coefficients[cur_index_in_coefficients]
                cur_index_in_coefficients += 1

        # ??
        # b_nat = deepcopy(b)
        b_nat = defaultdict(int)
        b0_nat = 0

        # 1
        for i in range(1, n_factors + 1):
            mult = b[(i,)] / intervals[i]
            b0_nat -= mult * x0s[i]

            b_nat[(i,)] += mult

        for i in range(1, n_factors + 1):
            for j in range(i + 1, n_factors + 1):
                mult = b[(i, j)] / (intervals[i] * intervals[j])
                b0_nat += mult * x0s[i] * x0s[j]

                b_nat[(i,)] -= mult * x0s[j]
                b_nat[(j,)] -= mult * x0s[i]

                b_nat[(i, j)] += mult

        for i in range(1, n_factors + 1):
            for j in range(i + 1, n_factors + 1):
                for k in range(j + 1, n_factors + 1):
                    mult = b[(i, j, k)] / (intervals[i] * intervals[j] * intervals[k])
                    b0_nat -= mult * x0s[i] * x0s[j] * x0s[k]

                    b_nat[(i,)] += mult * x0s[j] * x0s[k]
                    b_nat[(j,)] += mult * x0s[i] * x0s[k]
                    b_nat[(k,)] += mult * x0s[i] * x0s[j]

                    b_nat[(i, j)] -= mult * x0s[k]
                    b_nat[(i, k)] -= mult * x0s[j]
                    b_nat[(j, k)] -= mult * x0s[i]

                    # ??
                    # b_nat[(i, j, k)] = mult

        all_my_combinations.pop(3)
        b_nat_list = [b0_nat]
        for by, combinations_by in all_my_combinations.items():
            for combination in combinations_by:
                b_nat_list.append(b_nat[combination])

        needed_len = 0
        for i in range(n_factors + 1):
            needed_len += int(factorial(n_factors) / (factorial(i) * factorial(n_factors - i)))

        # needed_len = int((n_factors + 1) + (factorial(n_factors) / (factorial(n_factors - 2) * 2)))
        b_nat_list += [0] * (needed_len - len(b_nat_list))
        print(n_factors, needed_len)
        return b_nat_list

# def do_shit(n_factors, coefficients, intervals, x0s):
#     # забиваем пока на b0 вообще
#     b0_norm = coefficients.pop(0)
#
#     all_indexes = set(range(1, n_factors + 1))
#     by_range = list(range(1, n_factors + 1))  # комбинации по сколько индексов
#     all_my_combinations = {by: combinations(all_indexes, by) for by in by_range}  # комбинации по n индексов
#
#     # заполняем исходные (нормированные) коэффициенты
#     b_norm = dict()
#     cur_index_in_coefficients = 0
#     for by, combinations_by in all_my_combinations.items():
#         for combination_by in combinations_by:
#             b_norm[combination_by] = coefficients[cur_index_in_coefficients]
#             cur_index_in_coefficients += 1
#
#     # а теперь влияем на натуральные
#     b_nat = deepcopy(b_norm)
#
#     # по одному начинаются с +, по 2 - с минуса
#     start_sign = -1
#     for by_effecting in range(1, n_factors + 1):  # комбинации по effecting_by
#         start_sign *= -1
#         for combination_effecting in all_my_combinations[by_effecting]:
#             sign = -start_sign
#
#             mult = b_norm[combination_effecting]
#             for interval_index in combination_effecting:
#                 mult /= intervals[interval_index]
#
#             for by_being_changed in range(by_effecting, n_factors + 1):  # влияют на комбинации из такого же числа и выше
#                 sign *= -1
#
#
#
#
#
#     for by_to_change in by_range:  # сейчас будем влиять на натуральные коэффициенты по by_to_change индексов (вз/д)
#         for combination_to_change in all_my_combinations[by_to_change]: # вот на эти комбинации
#             sign = -1
#             for by_affecting in range(n_factors, by_to_change - 1, -1): # сейчас будем влиять с помощью комбинаций по by_affecting индексов
#
#                 for
#
#         for combination_by in combinations_by:
