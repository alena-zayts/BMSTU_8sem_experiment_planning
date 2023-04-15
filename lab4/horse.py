import numpy as np
from itertools import combinations
from math import factorial, sqrt
from collections import defaultdict
from copy import deepcopy

from lab4.queue import distributions
from lab4.queue.generator import Generator
from lab4.queue.modeller import Modeller
from lab4.queue.processor import Processor

FACTORS_NUMBER = 6
FREE_AMOUNT = 1

ONE_AMOUNT = FACTORS_NUMBER
TWO_AMOUNT = (FACTORS_NUMBER * (FACTORS_NUMBER - 1)) // 2
THREE_AMOUNT = FACTORS_NUMBER * (FACTORS_NUMBER - 1) * 
SQUARE_AMOUNT = FACTORS_NUMBER

COEFS_AMOUNT = FREE_AMOUNT + ONE_AMOUNT + TWO_AMOUNT + SQUARE_AMOUNT

n_SIZE_PFE = pow(2, FACTORS_NUMBER)
N_SIZE_OCKP = n_SIZE_PFE + 2 * FACTORS_NUMBER + 1

N_REPEATS = 1

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

        self.S = 1e10
        self.alpha = 1e10
        self.norm_full_results_table_OCKP = None
        self.norm_coefficients_OCKP = None
        self.nat_full_results_table_OCKP = None
        self.nat_coefficients_OCKP = None

        self.OCKP_natural_matrix = None
        self.OCKP_norm_matrix = None
        self.OCKP_column_names = None

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
        if lambda_ < 0 or mu < 0 or sigma < 0:
            print()
        return lambda_, mu, sigma

    def create_OCKP_plan_matrix(self):  # min_maxes: [[[min1, max1], [min2, max2], ...]
        self.S = sqrt(n_SIZE_PFE / N_SIZE_OCKP)
        self.alpha = sqrt(n_SIZE_PFE * (sqrt(N_SIZE_OCKP / n_SIZE_PFE) - 1) / 2)

        xs_column_names = ['x0'] + \
                          [f'x{factor_index}' for factor_index in range(1, FACTORS_NUMBER + 1)] + \
                          [''] * TWO_AMOUNT + \
                          [f'(x{factor_index})^2 - S' for factor_index in range(1, FACTORS_NUMBER + 1)]

        norm_row = (
                [1] +  # x0
                [0] * FACTORS_NUMBER +
                [0] * TWO_AMOUNT +
                [0] * SQUARE_AMOUNT
        )
        norm_matrix = np.array([norm_row for _ in range(N_SIZE_OCKP)], dtype=float)

        natural_row = (
                [1] +
                [0] * FACTORS_NUMBER +
                [0] * TWO_AMOUNT +
                [0] * SQUARE_AMOUNT
        )
        natural_matrix = np.array([natural_row for _ in range(N_SIZE_OCKP)], dtype=float)

        # ones (xi)
        for factor_index in range(1, FACTORS_NUMBER + 1):

            # first 2^m: as in OCKP
            period = pow(2, FACTORS_NUMBER - factor_index)

            for start_plus in range(period, n_SIZE_PFE, 2 * period):
                # add mins
                for row_number_min in range(start_plus - period, start_plus):
                    natural_matrix[row_number_min, factor_index] = self.min_maxes_nat[factor_index - 1][0]
                    norm_matrix[row_number_min, factor_index] = self.min_maxes_norm[factor_index - 1][0]


                # add maxes
                for row_number_max in range(start_plus, start_plus + period):
                    natural_matrix[row_number_max, factor_index] = self.min_maxes_nat[factor_index - 1][1]
                    norm_matrix[row_number_max, factor_index] = self.min_maxes_norm[factor_index - 1][1]

            # next 2m: like -alpha, +alpha
            row_for_minus_alpha = n_SIZE_PFE + 2 * (factor_index - 1)
            row_for_plus_alpha = row_for_minus_alpha + 1
            natural_matrix[row_for_minus_alpha, factor_index] = -self.alpha
            natural_matrix[row_for_plus_alpha, factor_index] = self.alpha
            norm_matrix[row_for_minus_alpha, factor_index] = -self.alpha
            norm_matrix[row_for_plus_alpha, factor_index] = self.alpha

            # next nc=m - zeroes

        # twos
        cur_factors_mult_index = FREE_AMOUNT + ONE_AMOUNT
        for factor_index1 in range(1, FACTORS_NUMBER + 1):
            for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER + 1):
                xs_column_names[cur_factors_mult_index] = f'x{factor_index1}x{factor_index2}'
                natural_matrix[:, cur_factors_mult_index] = natural_matrix[:, factor_index1] * \
                                                            natural_matrix[:, factor_index2]
                norm_matrix[:, cur_factors_mult_index] = norm_matrix[:, factor_index1] * norm_matrix[:, factor_index2]
                cur_factors_mult_index += 1

        # zi^2 - S
        for factor_index in range(1, FACTORS_NUMBER + 1):
            natural_matrix[:, FREE_AMOUNT + ONE_AMOUNT + TWO_AMOUNT + factor_index - 1] = \
                natural_matrix[:, factor_index] ** 2 - self.S

            norm_matrix[:, FREE_AMOUNT + ONE_AMOUNT + TWO_AMOUNT + factor_index - 1] = \
                norm_matrix[:, factor_index] ** 2 - self.S

        self.OCKP_natural_matrix = natural_matrix
        self.OCKP_norm_matrix = norm_matrix
        self.OCKP_column_names = xs_column_names + ['y', 'y_nl', '|y-ynl|']


    def process_results_OCKP(self, experiment_results: np.array):
        diag_free = 1 / N_SIZE_OCKP
        diag_ones = 1 / (n_SIZE_PFE + 2 * self.alpha)
        diag_twos = 1 / n_SIZE_PFE
        diag_squares = 1 / (2 * pow(self.alpha, 4))

        c_diag_elements = [diag_free] + [diag_ones] * ONE_AMOUNT + \
                          [diag_twos] * TWO_AMOUNT + [diag_squares] * SQUARE_AMOUNT

        norm_coefficients = [np.dot(self.OCKP_norm_matrix[:, i], experiment_results) * c_diag_elements[i]
                             for i in range(COEFS_AMOUNT)]

        norm_approximations = [sum(self.OCKP_norm_matrix[i, :] * norm_coefficients)
                               for i in range(N_SIZE_OCKP)]

        # concatenate
        norm_full_results = np.c_[self.OCKP_norm_matrix,
                                  experiment_results, norm_approximations,
                                  np.abs(experiment_results - norm_approximations)]

        self.norm_full_results_table_OCKP = norm_full_results
        self.norm_coefficients_OCKP = norm_coefficients

        # TODO
        self.nat_full_results_table_OCKP = norm_full_results
        self.nat_coefficients_OCKP = norm_coefficients

    def run_OCKP(self):
        self.create_OCKP_plan_matrix()

        # print(plan_matrix_normalized)
        experiment_results = np.zeros(N_SIZE_OCKP)

        for exp_number, exp_params in enumerate(self.OCKP_norm_matrix):
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

        self.process_results_OCKP(experiment_results)

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

        experiment_plan_row_norm_OCKP = np.array(
            [1] +
            [gen_int_normalized, proc_int_normalized, proc_var_normalized, gen_int_normalized2, proc_int_normalized2,
             proc_var_normalized2] +
            [0] * (TWO_AMOUNT + SQUARE_AMOUNT)
        )

        experiment_plan_row_nat_OCKP = np.array(
            [1] +
            [gen_int_nat, proc_int_nat, proc_var_nat, gen_int2_nat, proc_int2_nat, proc_var2_nat] +
            [0] * (TWO_AMOUNT + SQUARE_AMOUNT)
        )

        # twos
        cur_factors_mult_index = FACTORS_NUMBER + 1
        for factor_index1 in range(1, FACTORS_NUMBER + 1):
            for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER + 1):
                experiment_plan_row_norm_OCKP[cur_factors_mult_index] = (experiment_plan_row_norm_OCKP[factor_index1] *
                                                                         experiment_plan_row_norm_OCKP[factor_index2])
                experiment_plan_row_nat_OCKP[cur_factors_mult_index] = (experiment_plan_row_nat_OCKP[factor_index1] *
                                                                        experiment_plan_row_nat_OCKP[factor_index2])
                cur_factors_mult_index += 1

        # zi^2 - S
        for factor_index in range(1, FACTORS_NUMBER + 1):
            experiment_plan_row_norm_OCKP[FREE_AMOUNT + ONE_AMOUNT + TWO_AMOUNT + factor_index - 1] = \
                experiment_plan_row_norm_OCKP[FACTORS_NUMBER] ** 2 - self.S

            experiment_plan_row_nat_OCKP[FREE_AMOUNT + ONE_AMOUNT + TWO_AMOUNT + factor_index - 1] = \
                experiment_plan_row_nat_OCKP[:, FACTORS_NUMBER] ** 2 - self.S

        experiment_plan_row_norm_OCKP = np.array(experiment_plan_row_norm_OCKP)
        experiment_plan_row_nat_OCKP = np.array(experiment_plan_row_nat_OCKP)

        nonlinear_approximation_norm_OCKP = sum(experiment_plan_row_norm_OCKP * self.norm_coefficients_OCKP)
        nonlinear_approximation_nat_OCKP = sum(experiment_plan_row_nat_OCKP * self.nat_coefficients_OCKP)

        total_norm_OCKP = list(experiment_plan_row_norm_OCKP)
        total_nat_OCKP = list(experiment_plan_row_nat_OCKP)

        total_norm_OCKP.extend([
            experiment_result, nonlinear_approximation_norm_OCKP,
            np.abs(experiment_result - nonlinear_approximation_norm_OCKP)])

        total_nat_OCKP.extend([
            experiment_result, nonlinear_approximation_nat_OCKP,
            np.abs(experiment_result - nonlinear_approximation_nat_OCKP)])

        self.norm_full_results_table_OCKP = np.r_[self.norm_full_results_table_OCKP, [total_norm_OCKP]]
        self.nat_full_results_table_OCKP = np.r_[self.nat_full_results_table_OCKP, [total_nat_OCKP]]

    def norm_to_natural_coefficients(self, norm_coefficients, n_factors):
        norm_coefficients = list(norm_coefficients)

        x0s = [None, ] + [(self.min_maxes_nat[i][1] + self.min_maxes_nat[i][0]) / 2 for i in range(n_factors)]
        intervals = [None, ] + [(self.min_maxes_nat[i][1] - self.min_maxes_nat[i][0]) / 2 for i in range(n_factors)]

        b0_nat = norm_coefficients.pop(0)

        all_indexes = set(range(1, n_factors + 1))
        all_my_combinations = {by: list(combinations(all_indexes, by)) for by in
                               range(1, 4)}  # комбинации по n индексов

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
