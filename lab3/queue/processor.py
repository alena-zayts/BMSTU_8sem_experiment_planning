from lab3.queue import distributions

from typing import List


class Processor:
    def __init__(self,
                 time_distributions: List[distributions.AbstractDistribution]) -> None:
        self._time_distributions = time_distributions
        self.current_queue_size = 0
        self.max_queue_size = 0
        self.processed_requests = 0
        self.time_periods = []
        self.requests_types_to_process = []

    def process(self) -> None:
        if self.current_queue_size <= 0:
            raise ValueError

        self.processed_requests += 1
        self.current_queue_size -= 1

    def receive_request(self, request_type: int) -> None:
        self.current_queue_size += 1
        self.requests_types_to_process.append(request_type)
        if self.current_queue_size > self.max_queue_size:
            self.max_queue_size = self.current_queue_size

    def generate_time_period(self) -> float:
        assert (0 < self.current_queue_size == len(self.requests_types_to_process))
        next_request_type = self.requests_types_to_process.pop(0)
        time = self._time_distributions[next_request_type].generate_time()
        self.time_periods.append(time)
        return time
