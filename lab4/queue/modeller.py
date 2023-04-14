from typing import List, Union

from lab4.queue.generator import Generator
from lab4.queue.processor import Processor

EPS = 1e-6

class Modeller:
    def __init__(self, generators: List[Generator], processor: Processor):
        self._generators = generators
        self._processor = processor

    def event_modelling(self, end_param: Union[float, int]):
        processor = self._processor
        generators = self._generators

        for generator in self._generators:
            generator.set_receivers([processor])

        types_times_generated = []
        types_times_started_processing = []
        types_times_ended_processing = []

        generators_next_times = [generator.generate_time_period() for generator in generators]
        processor_next_time = min(generators_next_times)

        current_modeling_time = 0
        while len(types_times_ended_processing) < end_param:
            min_generator_next_time = min(generators_next_times)

            if min_generator_next_time < processor_next_time + EPS:
                generator_index = generators_next_times.index(min_generator_next_time)

                types_times_generated.append([generator_index, min_generator_next_time])
                current_modeling_time = min_generator_next_time
                generators_next_times[generator_index] += generators[generator_index].generate_time_period()
                processor.receive_request(generator_index)

            else:
                if processor.current_queue_size > 0:
                    current_request_type_to_process = processor.requests_types_to_process[0]
                    types_times_started_processing.append([current_request_type_to_process, processor_next_time])
                    current_modeling_time = processor_next_time
                    processor_next_time += processor.generate_time_period()
                    types_times_ended_processing.append([current_request_type_to_process, processor_next_time])
                    processor.process()
                else:
                    processor_next_time = min_generator_next_time

        if (
                len(types_times_generated) < len(types_times_started_processing) or
                len(types_times_started_processing) < len(types_times_ended_processing)
        ):
            raise ValueError

        times_in_queue = [types_times_started_processing[i][1] - types_times_generated[i][1]
                          for i in range(len(types_times_started_processing))]
        mean_time_in_queue = sum(times_in_queue) / len(times_in_queue)

        times_in_processor = [types_times_ended_processing[i][1] - types_times_started_processing[i][1]
                              for i in range(len(types_times_ended_processing))]
        mean_time_in_processor = sum(times_in_processor) / len(times_in_processor)

        times_in_smo = [types_times_ended_processing[i][1] - types_times_generated[i][1]
                        for i in range(len(types_times_ended_processing))]
        mean_time_in_smo = sum(times_in_smo) / len(times_in_smo)

        p_fact2 = sum(processor.time_periods) / current_modeling_time

        result = {
            'processed_requests': len(types_times_ended_processing),
            'modeling_time': current_modeling_time,
            'p_fact': p_fact2,
            'mean_time_in_queue': mean_time_in_queue,
            'mean_time_in_smo': mean_time_in_smo,
        }

        return result
