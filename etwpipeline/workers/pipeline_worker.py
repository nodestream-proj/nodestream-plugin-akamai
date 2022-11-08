from threading import Thread

from .pipeline_job import PipelineJob


class PipelineWorker:
    def __init__(self, pipeline_job: PipelineJob):
        self.job = pipeline_job

    def start(self):
        # The entire Python program exits when no alive non-daemon
        # threads are left. If for some reason the main thread is terminated,
        # these threads will be killed when the process is killed.
        self.thread = Thread(
            target=self.job.do_job_until_successfully_complete, daemon=True
        )
        self.thread.start()

    def get_state(self):
        return self.job.get_state()
