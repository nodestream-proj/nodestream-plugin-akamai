class WorkerGroup:
    def __init__(self, workers) -> None:
        self.workers = workers

    def start(self):
        for worker in self.workers:
            worker.start()

    def get_state(self):
        return [worker.get_state() for worker in self.workers]

    def all_done(self):
        return all(worker_status["terminated"] for worker_status in self.get_state())

    def any_unhealthy(self):
        return any(
            worker_status["in_error_state"] for worker_status in self.get_state()
        )
