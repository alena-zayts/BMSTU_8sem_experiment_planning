from lab3.queue.processor import Processor
from lab3.queue.generator import Generator
from lab3.queue.modeller import Modeller
from lab3.queue import distributions
import numpy as np

FACTORS_NUMBER = 6
M_SIZE = 2 ** FACTORS_NUMBER

LIN_COEFS_AMOUNT = FACTORS_NUMBER + 1
NONLIN_COEFS_AMOUNT = M_SIZE

N_REPEATS = 1


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

    def process_results(self, experiment_results: np.array):
        # b = [X^T * X]^-1  * X^T * y_exp
        x = self.PFE_norm_matrix
        norm_coefficients = np.dot(np.dot(np.linalg.inv(np.dot(np.transpose(x), x)), np.transpose(x)),
                                   experiment_results)

        x = self.PFE_natural_matrix
        nat_coefficients = np.dot(np.dot(np.linalg.inv(np.dot(np.transpose(x), x)), np.transpose(x)),
                                  experiment_results)
        #print()

        # norm_coefficients = np.dot(np.invert(x), experiment_results)

        # norm_coefficients = np.array([
        #     np.mean((experiment_plan_matrix[:, j] * experiment_results))
        #     for j in range(M_SIZE)])
        # print(norm_coefficients)

        # norm_coefficients = np.array([
        #     np.mean((np.linalg.inv(experiment_plan_matrix)[:, j] * experiment_results))
        #     for j in range(M_SIZE)])
        # print(norm_coefficients)

        norm_nonlinear_approximations = [
            sum(self.PFE_norm_matrix[i, :] * norm_coefficients[:])
            for i in range(M_SIZE)]
        norm_linear_approximations = [
            sum(self.PFE_norm_matrix[i, :LIN_COEFS_AMOUNT] * norm_coefficients[:LIN_COEFS_AMOUNT])
            for i in range(M_SIZE)]

        nat_nonlinear_approximations = [
            sum(self.PFE_natural_matrix[i, :] * nat_coefficients[:])
            for i in range(M_SIZE)]
        nat_linear_approximations = [
            sum(self.PFE_natural_matrix[i, :LIN_COEFS_AMOUNT] * nat_coefficients[:LIN_COEFS_AMOUNT])
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

        self.norm_full_results_table = norm_full_results
        self.norm_coefficients = norm_coefficients

        self.nat_full_results_table = nat_full_results
        self.nat_coefficients = nat_coefficients

        self.PFE_column_names += ['y', 'y_l', 'y_nl', '|y-yl|', '|y-ynl|']

    def nat_factor_from_norm(self, x_norm, xmin_nat, xmax_nat):
        return x_norm * (xmax_nat - xmin_nat) / 2 + (xmax_nat + xmin_nat) / 2

    def norm_factor_from_nat(self, x_nat, xmin_nat, xmax_nat):
        x0 = (xmin_nat + xmax_nat) / 2
        interval = (xmax_nat - xmin_nat) / 2
        return (x_nat - x0) / interval

    def run(self):
        # print(plan_matrix_normalized)
        experiment_results = np.zeros(M_SIZE)

        for exp_number, exp_params in enumerate(self.PFE_norm_matrix):
            gen_int = self.nat_factor_from_norm(exp_params[1], self.global_gen_int_min, self.global_gen_int_max)
            proc_int = self.nat_factor_from_norm(exp_params[2], self.global_proc_int_min, self.global_proc_int_max)
            proc_var = self.nat_factor_from_norm(exp_params[3], self.global_proc_var_min, self.global_proc_var_max)
            gen_int2 = self.nat_factor_from_norm(exp_params[4], self.global_gen_int_min, self.global_gen_int_max)
            proc_int2 = self.nat_factor_from_norm(exp_params[5], self.global_proc_int_min, self.global_proc_int_max)
            proc_var2 = self.nat_factor_from_norm(exp_params[6], self.global_proc_var_min, self.global_proc_var_max)

            lambda_, mu, sigma = gen_int, 1 / proc_int, proc_var
            lambda_2, mu2, sigma2 = gen_int2, 1 / proc_int2, proc_var2

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

        self.process_results(experiment_results)

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

        lambda_, mu, sigma = gen_int_nat, 1 / proc_int_nat, proc_var_nat
        lambda_2, mu2, sigma2 = gen_int2_nat, 1 / proc_int2_nat, proc_var2_nat

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

        experiment_plan_row_norm = np.array(
            [1] +
            [gen_int_normalized, proc_int_normalized, proc_var_normalized, gen_int_normalized2, proc_int_normalized2,
             proc_var_normalized2, ] +
            [1] * (M_SIZE - FACTORS_NUMBER - 1)

        )
        experiment_plan_row_nat = np.array(
            [1] +
            [gen_int_nat, proc_int_nat, proc_var_nat, gen_int2_nat, proc_int2_nat,
             proc_var2_nat, ] +
            [1] * (M_SIZE - FACTORS_NUMBER - 1)
        )

        # 2
        cur_factors_mult_index = 7
        for factor_index1 in range(1, FACTORS_NUMBER):
            for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER + 1):
                experiment_plan_row_norm[cur_factors_mult_index] = (experiment_plan_row_norm[factor_index1] *
                                                                    experiment_plan_row_norm[factor_index2])
                experiment_plan_row_nat[cur_factors_mult_index] = (experiment_plan_row_nat[factor_index1] *
                                                                   experiment_plan_row_nat[factor_index2])
                cur_factors_mult_index += 1

        # 3
        for factor_index1 in range(1, FACTORS_NUMBER - 1):
            for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER):
                for factor_index3 in range(factor_index2 + 1, FACTORS_NUMBER + 1):
                    experiment_plan_row_norm[cur_factors_mult_index] = (experiment_plan_row_norm[factor_index1] *
                                                                        experiment_plan_row_norm[factor_index2] *
                                                                        experiment_plan_row_norm[factor_index3])
                    experiment_plan_row_nat[cur_factors_mult_index] = (experiment_plan_row_nat[factor_index1] *
                                                                        experiment_plan_row_nat[factor_index2] *
                                                                        experiment_plan_row_nat[factor_index3])
                    cur_factors_mult_index += 1

        # 4
        for factor_index1 in range(1, FACTORS_NUMBER - 2):
            for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER - 1):
                for factor_index3 in range(factor_index2 + 1, FACTORS_NUMBER):
                    for factor_index4 in range(factor_index3 + 1, FACTORS_NUMBER + 1):
                        experiment_plan_row_norm[cur_factors_mult_index] = (experiment_plan_row_norm[factor_index1] *
                                                                            experiment_plan_row_norm[factor_index2] *
                                                                            experiment_plan_row_norm[factor_index3] *
                                                                            experiment_plan_row_norm[factor_index4])
                        experiment_plan_row_nat[cur_factors_mult_index] = (experiment_plan_row_nat[factor_index1] *
                                                                            experiment_plan_row_nat[factor_index2] *
                                                                            experiment_plan_row_nat[factor_index3] *
                                                                            experiment_plan_row_nat[factor_index4])
                        cur_factors_mult_index += 1

        # 5
        for factor_index1 in range(1, FACTORS_NUMBER - 3):
            for factor_index2 in range(factor_index1 + 1, FACTORS_NUMBER - 2):
                for factor_index3 in range(factor_index2 + 1, FACTORS_NUMBER - 1):
                    for factor_index4 in range(factor_index3 + 1, FACTORS_NUMBER):
                        for factor_index5 in range(factor_index4 + 1, FACTORS_NUMBER + 1):
                            experiment_plan_row_norm[cur_factors_mult_index] = (
                                        experiment_plan_row_norm[factor_index1] *
                                        experiment_plan_row_norm[factor_index2] *
                                        experiment_plan_row_norm[factor_index3] *
                                        experiment_plan_row_norm[factor_index4] *
                                        experiment_plan_row_norm[factor_index5])
                            experiment_plan_row_nat[cur_factors_mult_index] = (
                                        experiment_plan_row_nat[factor_index1] *
                                        experiment_plan_row_nat[factor_index2] *
                                        experiment_plan_row_nat[factor_index3] *
                                        experiment_plan_row_nat[factor_index4] *
                                        experiment_plan_row_nat[factor_index5])
                            cur_factors_mult_index += 1

        assert cur_factors_mult_index == M_SIZE - 1
        experiment_plan_row_norm[cur_factors_mult_index] = (experiment_plan_row_norm[1] * experiment_plan_row_norm[2] *
                                                            experiment_plan_row_norm[3] * experiment_plan_row_norm[4] *
                                                            experiment_plan_row_norm[5] * experiment_plan_row_norm[6])
        experiment_plan_row_nat[cur_factors_mult_index] = (experiment_plan_row_nat[1] * experiment_plan_row_nat[2] *
                                                            experiment_plan_row_nat[3] * experiment_plan_row_nat[4] *
                                                            experiment_plan_row_nat[5] * experiment_plan_row_nat[6])
        experiment_plan_row_norm = np.array(experiment_plan_row_norm)
        experiment_plan_row_nat = np.array(experiment_plan_row_nat)

        nonlinear_approximation_norm = sum(experiment_plan_row_norm * self.norm_coefficients)
        nonlinear_approximation_nat = sum(experiment_plan_row_nat * self.nat_coefficients)

        linear_approximation_norm = sum(experiment_plan_row_norm[:LIN_COEFS_AMOUNT] * self.norm_coefficients[:LIN_COEFS_AMOUNT])
        linear_approximation_nat = sum(experiment_plan_row_nat[:LIN_COEFS_AMOUNT] * self.nat_coefficients[:LIN_COEFS_AMOUNT])

        total_norm = list(experiment_plan_row_norm)
        total_nat = list(experiment_plan_row_nat)

        total_norm.extend([
            experiment_result, linear_approximation_norm, nonlinear_approximation_norm,
            np.abs(experiment_result - linear_approximation_norm),
            np.abs(experiment_result - nonlinear_approximation_norm)])

        total_nat.extend([
            experiment_result, linear_approximation_nat, nonlinear_approximation_nat,
            np.abs(experiment_result - linear_approximation_nat),
            np.abs(experiment_result - nonlinear_approximation_nat)])

        self.norm_full_results_table = np.r_[self.norm_full_results_table, [total_norm]]
        self.nat_full_results_table = np.r_[self.nat_full_results_table, [total_nat]]
