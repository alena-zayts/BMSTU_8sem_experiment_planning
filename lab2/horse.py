from lab2.queue.processor import Processor
from lab2.queue.generator import Generator
from lab2.queue.modeller import Modeller
from lab2.queue import distributions
import numpy as np

FACTORS_NUMBER = 3
M_SIZE = 2 ** FACTORS_NUMBER

LIN_COEFS_AMOUNT = FACTORS_NUMBER + 1
NONLIN_COEFS_AMOUNT = M_SIZE

N_REPEATS = 3


class Horse:
    def __init__(self, gen_int_min, gen_int_max, proc_int_min, proc_int_max, proc_var_min, proc_var_max,
                 requests_amount):
        self.gen_int_min = gen_int_min
        self.gen_int_max = gen_int_max

        self.proc_int_min = proc_int_min
        self.proc_int_max = proc_int_max
        self.proc_var_min = proc_var_min
        self.proc_var_max = proc_var_max

        self.requests_amount = requests_amount
        self.coefficients = []

    def create_plan_matrix(self):
        matrix = np.array([[1] * M_SIZE for _ in range(M_SIZE)])

        for j in range(1, FACTORS_NUMBER + 1):
            period = pow(2, FACTORS_NUMBER - j)
            for start_minus in range(period, M_SIZE, 2 * period):
                for i in range(start_minus, start_minus + period):
                    matrix[i][j] = -1
        # pairs
        matrix[:, 4] = matrix[:, 1] * matrix[:, 2]
        matrix[:, 5] = matrix[:, 1] * matrix[:, 3]
        matrix[:, 6] = matrix[:, 2] * matrix[:, 3]

        # triplets
        matrix[:, 7] = matrix[:, 1] * matrix[:, 2] * matrix[:, 3]

        return matrix

    def process_results(self, experiment_plan_matrix: np.array, experiment_results: np.array):
        coefficients = np.array([
            np.mean((experiment_plan_matrix[:, j] * experiment_results))
            for j in range(M_SIZE)])

        nonlinear_approximations = [
            sum(experiment_plan_matrix[i, :] * coefficients[:])
            for i in range(M_SIZE)]
        linear_approximations = [
            sum(experiment_plan_matrix[i, :LIN_COEFS_AMOUNT] * coefficients[:LIN_COEFS_AMOUNT])
            for i in range(M_SIZE)]

        # concatenate
        full_results = np.c_[experiment_plan_matrix,
                             experiment_results, linear_approximations, nonlinear_approximations,
                             np.abs(experiment_results - linear_approximations),
                             np.abs(experiment_results - nonlinear_approximations)]

        return full_results, coefficients

    def natural_factor_from_normalized(self, x_norm, xmin, xmax):
        return x_norm * (xmax - xmin) / 2 + (xmax + xmin) / 2

    def run(self):
        plan_matrix_normalized = self.create_plan_matrix()
        # print(plan_matrix_normalized)
        experiment_results = np.zeros(M_SIZE)

        for experiment_number, experiment_params in enumerate(plan_matrix_normalized):
            gen_int = self.natural_factor_from_normalized(experiment_params[1], self.gen_int_min, self.gen_int_max)
            proc_int = self.natural_factor_from_normalized(experiment_params[2], self.proc_int_min, self.proc_int_max)
            proc_var = self.natural_factor_from_normalized(experiment_params[3], self.proc_var_min, self.proc_var_max)

            lambda_, mu, sigma = gen_int, 1 / proc_int, proc_var
            cur_experiment_results = []
            for _ in range(N_REPEATS):
                generators = [Generator(distributions.ExponentialDistribution(lambda_))]
                processors = [Processor(distributions.NormalDistribution(mu, sigma))]
                modeller = Modeller(generators, processors)
                cur_experiment_results.append(modeller.event_modelling(self.requests_amount)['mean_time_in_queue'])

            experiment_results[experiment_number] = sum(cur_experiment_results) / N_REPEATS

        full_results_table, self.coefficients = self.process_results(plan_matrix_normalized, experiment_results)

        return full_results_table, self.coefficients

    def check(self, gen_int_normalized, proc_int_normalized, proc_var_normalized):

        gen_int = self.natural_factor_from_normalized(gen_int_normalized, self.gen_int_min, self.gen_int_max)
        proc_int = self.natural_factor_from_normalized(proc_int_normalized, self.proc_int_min, self.proc_int_max)
        proc_var = self.natural_factor_from_normalized(proc_var_normalized, self.proc_var_min, self.proc_var_max)

        lambda_, mu, sigma = gen_int, 1 / proc_int, proc_var

        cur_experiment_results = []
        for _ in range(N_REPEATS):
            generators = [Generator(distributions.ExponentialDistribution(lambda_))]
            processors = [Processor(distributions.NormalDistribution(mu, sigma))]
            modeller = Modeller(generators, processors)
            cur_experiment_results.append(modeller.event_modelling(self.requests_amount)['mean_time_in_queue'])

        experiment_result = sum(cur_experiment_results) / N_REPEATS
        experiment_plan_row = np.array([1, gen_int_normalized, proc_int_normalized, proc_var_normalized,
                                        gen_int_normalized * proc_int_normalized,
                                        gen_int_normalized * proc_var_normalized,
                                        proc_int_normalized * proc_var_normalized,
                                        gen_int_normalized * proc_int_normalized * proc_var_normalized])
        nonlinear_approximation = sum(experiment_plan_row * self.coefficients)
        linear_approximation = sum(experiment_plan_row[:LIN_COEFS_AMOUNT] * self.coefficients[:LIN_COEFS_AMOUNT])
        total = list(experiment_plan_row)
        total.extend([
                     experiment_result, linear_approximation, nonlinear_approximation,
                     np.abs(experiment_result - linear_approximation),
                     np.abs(experiment_result - nonlinear_approximation)])

        return np.array(total)
