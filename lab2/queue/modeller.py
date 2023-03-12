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

        p_fact2 = sum(processor.time_periods) / current_modeling_time

        result = {
            'processed_requests': len(times_ended_processing),
            'modeling_time': current_modeling_time,
            'p_fact': p_fact2,
            'mean_time_in_queue': mean_time_in_queue,
            'mean_time_in_smo': mean_time_in_smo,
        }

        return result
