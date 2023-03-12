from typing import List, Union

from lab1.generator import Generator
from lab1.processor import Processor


class Modeller:
    def __init__(self, generators: List[Generator], processors: List[Processor]):
        self._generators = generators
        self._processors = processors

    def still_working(self, how_to_check: str, end_param: Union[float, int],
                      current_modelling_time: Union[float, int], processed_requests: int):
        if how_to_check == 'time':
            return current_modelling_time < end_param
        elif how_to_check == 'requests':
            return processed_requests < end_param
        else:
            raise ValueError

    def event_modelling(self, how_to_check: str, end_param: Union[float, int]):
        generator = self._generators[0]
        processor = self._processors[0]
        generator.set_receivers([processor])

        times_generated = []
        times_started_processing = []
        times_ended_processing = []

        generator_next_time = generator.generate_time_period()
        generator_next_times = [generator_next_time]
        times_started_processing.append(generator_next_time)
        processor_next_time = generator_next_time + processor.generate_time_period()
        processor_next_times = [processor_next_time]

        current_modeling_time = 0
        while self.still_working(how_to_check, end_param, current_modeling_time, len(times_ended_processing)):
            generator_next_time = generator_next_times[0]
            processor_next_time = processor_next_times[0]

            if generator_next_time < processor_next_time:
                times_generated.append(generator_next_time)
                current_modeling_time = generator_next_time
                generator_next_times.pop(0)
                generator_next_time += generator.generate_time_period()
                generator_next_times.append(generator_next_time)
            else:
                times_started_processing.append(processor_next_time)
                current_modeling_time = processor_next_time
                processor_next_times.pop(0)
                processor_next_time += processor.generate_time_period()
                processor_next_times.append(processor_next_time)
                times_ended_processing.append(processor_next_time)



        if len(times_generated) < len(times_started_processing) or len(times_started_processing) < len(times_ended_processing):
            if len(times_started_processing) == len(times_generated) + 1:
                times_started_processing.pop(-1)
            else:
                raise ValueError


        times_in_queue = [times_started_processing[i] - times_generated[i] for i in range(len(times_started_processing))]
        mean_time_in_queue = sum(times_in_queue) / len(times_in_queue)

        times_in_processor = [times_ended_processing[i] - times_started_processing[i] for i in range(len(times_ended_processing))]
        mean_time_in_processor = sum(times_in_processor) / len(times_in_processor)

        times_in_smo = [times_ended_processing[i] - times_generated[i] for i in range(len(times_ended_processing))]
        mean_time_in_smo = sum(times_in_smo) / len(times_in_smo)

        # 3
        p_fact2 = sum(processor.time_periods) / current_modeling_time


        result = {
            'processed_requests': len(times_ended_processing),
            'modeling_time': current_modeling_time,
            'p_fact': p_fact2,
            'mean_time_in_queue': mean_time_in_queue,
            'mean_time_in_smo': mean_time_in_smo,
        }

        return result

    def delta_t_modelling(self, how_to_check: str, end_param: Union[float, int]):
        generator = self._generators[0]
        processor = self._processors[0]
        generator.set_receivers([processor])

        times_generated = []
        times_started_processing = []
        times_ended_processing = []

        generator_next_time = generator.generate_time_period()
        times_started_processing.append(generator_next_time)
        processor_next_time = generator_next_time + processor.generate_time_period()

        current_modeling_time = 0
        dt = 0.01

        while self.still_working(how_to_check, end_param, current_modeling_time, len(times_ended_processing)):

            if generator_next_time <= current_modeling_time:
                times_generated.append(generator_next_time)
                generator.generate_request()
                generator_next_time += generator.generate_time_period()

            if processor_next_time <= current_modeling_time:

                if processor.current_queue_size > 0:
                    processor.process()
                    times_ended_processing.append(processor_next_time)

                if processor.current_queue_size > 0:
                    times_started_processing.append(processor_next_time)
                    processor_next_time = processor_next_time + processor.generate_time_period()
                else:
                    processor_next_time = generator_next_time + processor.generate_time_period()
                    times_started_processing.append(generator_next_time)

            current_modeling_time += dt

        if len(times_generated) < len(times_started_processing) or len(times_started_processing) < len(times_ended_processing):
            if len(times_started_processing) == len(times_generated) + 1:
                times_started_processing.pop(-1)
            else:
                raise ValueError


        times_in_queue = [times_started_processing[i] - times_generated[i] for i in range(len(times_started_processing))]
        mean_time_in_queue = sum(times_in_queue) / len(times_in_queue)

        times_in_processor = [times_ended_processing[i] - times_started_processing[i] for i in range(len(times_ended_processing))]
        mean_time_in_processor = sum(times_in_processor) / len(times_in_processor)

        times_in_smo = [times_ended_processing[i] - times_generated[i] for i in range(len(times_ended_processing))]
        mean_time_in_smo = sum(times_in_smo) / len(times_in_smo)

        # 3
        p_fact2 = sum(processor.time_periods) / current_modeling_time
        # 2
        # lambda_fact2 = 1 / (sum(generator.time_periods) / len(generator.time_periods))
        # mu_fact2 = 1 / (sum(processor.time_periods) / len(processor.time_periods))
        # p_fact2 = lambda_fact2 / mu_fact2
        # 1
        # lambda_fact = len(times_generated) / current_modeling_time
        # mu_fact = 1 / mean_time_in_processor
        # p_fact = lambda_fact / mu_fact
        # print(f'Экспериментальные: lambda {lambda_fact}, mu {mu_fact}')


        # print(lambda_fact, mu_fact, p_fact)
        # print(lambda_fact2, mu_fact2, p_fact2)
        # print()

        # plt.plot(times_generated, label='times_generated')
        # plt.plot(times_started_processing, label='times_started_processing')
        # plt.plot(times_ended_processing, label='times_ended_processing')

        # plt.plot(times_in_queue, label='times_in_queue')
        # plt.plot(times_in_processor, label='times_in_processor')
        # plt.plot(times_in_smo, label='times_in_smo')
        # plt.legend()
        # plt.show()


        result = {
            'processed_requests': len(times_ended_processing),
            'modeling_time': current_modeling_time,
            'p_fact': p_fact2,
            'mean_time_in_queue': mean_time_in_queue,
            'mean_time_in_smo': mean_time_in_smo,
        }

        return result