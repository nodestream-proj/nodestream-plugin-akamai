import datetime
import logging
import queue
import threading


class ThreadedWorkerGroup:
    def __init__(self, thread_count=16):
        self.threads = []
        self.thread_count = thread_count

    def start(self, target, items):
        self.target = target
        self.item_queue = queue.Queue()
        self.start_time = datetime.datetime.now()

        for item in items:
            self.item_queue.put_nowait(item)

        for x in range(0, min(len(items), self.thread_count)):
            t = threading.Thread(target=self.do_work)
            self.threads.append(t)

        for x in self.threads:
            x.start()

    def is_alive(self):
        return any(thread.is_alive() for thread in self.threads)

    def wait_for_end(self):
        for x in self.threads:
            x.join()

        logging.debug(f"Done {datetime.datetime.now() - self.start_time}")

    def do_work(self):
        items_processed = []
        while True:
            try:
                item = self.item_queue.get(True, 0.1)
                items_processed.append(item)
                self.target(item)
                self.item_queue.task_done()
            except queue.Empty:
                break

        logging.debug(
            f"Worker finished processing {len(items_processed)} items in {datetime.datetime.now() - self.start_time}"
        )
