import json
from abc import ABC, abstractmethod
from logging import INFO, getLevelName, getLogger


class Writer(ABC):
    @abstractmethod
    def write_item(self, item):
        raise NotImplementedError

    def batch_write(self, items):
        for item in items:
            self.write_item(item)

    def finish(self):
        pass


class LoggerWriter(Writer):
    def __init__(self, logger_name=None, level=INFO) -> None:
        logger_name = logger_name or self.__class__.__name__
        self.logger = getLogger(logger_name)
        # At first glance this line would appear wrong. `getLevelName` does the
        # mapping bi-directionally. If you give it a number (level), you get the name
        # and vice-versa. Since we are standardizing on the int representation of
        # the level (thats what Logger#log requires), then we need to
        # call `getLevelName` when the value is the string name for the log level.
        #
        # see: https://docs.python.org/3/library/logging.html#logging.getLevelName
        self.level = getLevelName(level) if isinstance(level, str) else level

    def write_item(self, item):
        self.logger.log(self.level, item)


class JsonFileWriter(Writer):
    def __init__(self, file_name: str, **json_extra_args) -> None:
        self.file_name = file_name
        self.fp = None
        self.json_extra_args = json_extra_args

    def write_item(self, item):
        if self.fp is None:
            self.fp = open(self.file_name, "w")
            self.fp.write("[\n")
        else:
            self.fp.write(",\n")

        json.dump(item, self.fp, default=str, indent=2, **self.json_extra_args)

    def finish(self):
        if self.fp is not None:
            self.fp.write("\n]\n")
            self.fp.close()
            self.fp = None


class TallyLoggerWriter(LoggerWriter):
    def __init__(self):
        self.tally_count = 0
        super().__init__()

    def write_item(self, item):
        self.tally_count += 1
        super().write_item(self.tally_count)

    def batch_write(self, items):
        self.tally_count += len(items)
        super().write_item(self.tally_count)
