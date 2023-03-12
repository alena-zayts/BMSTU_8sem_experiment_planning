from lab2.queue import distributions


class Processor:
    def __init__(self, time_distribution: distributions.AbstractDistribution) -> None:
        self._time_distribution = time_distribution
        self.current_queue_size = 0
        self.max_queue_size = 0
        self.processed_requests = 0
        self.time_periods = []

    def process(self) -> None:
        if self.current_queue_size <= 0:
            raise ValueError

        self.processed_requests += 1
        self.current_queue_size -= 1

    def receive_request(self) -> None:
        self.current_queue_size += 1
        if self.current_queue_size > self.max_queue_size:
            self.max_queue_size = self.current_queue_size

    def generate_time_period(self) -> float:
        time = self._time_distribution.generate_time()
        self.time_periods.append(time)
        return time
