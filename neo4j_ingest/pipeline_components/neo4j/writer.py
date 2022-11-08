from abc import abstractmethod
from contextlib import contextmanager
from functools import cache
from logging import getLogger
from typing import List

from etwpipeline.writers import Writer
from neo4j import GraphDatabase, Query, Transaction

from .ingest_strategy import DesiredIngestion, Neo4jIngestionStrategy


# We cache and use a single driver for better connection reuse.
# One per thread means we need to juggle more connections per pod.
# better to reuse them between each thread. Both `cache` and `GraphDatabase` are
# inherently thread safe.
@cache
def get_driver(uri, username, password):
    return GraphDatabase.driver(uri, auth=(username, password))


class BaseNeo4jWriter(Writer):
    @classmethod
    def __declarative_init__(
        cls, uri, username, password, database_name=None, **kwargs
    ):
        driver = get_driver(uri, username, password)
        return cls(driver, database_name, **kwargs)

    def __init__(self, driver, database_name):
        self.driver = driver
        self.database_name = database_name
        self.logger = getLogger(self.__class__.__name__)

    def write_item(self, item):
        return self.batch_write([item])

    def finish(self):
        self.driver.close()

    @contextmanager
    def session(self):
        with self.driver.session(database=self.database_name) as session:
            yield session


class TransactionalNeo4jWriter(BaseNeo4jWriter):
    def batch_write(self, items):
        self.logger.info("Starting to write batch of '%d' items to neo4j", len(items))
        with self.session() as session:
            session.write_transaction(self.write_with_transaction, items)
        self.logger.info("Successfully wrote batch of '%d' items to neo4j", len(items))

    @abstractmethod
    def write_with_transaction(self, transaction: Transaction, items):
        raise NotImplementedError


class IngestNeo4jWriter(TransactionalNeo4jWriter):
    def write_with_transaction(
        self, transaction: Transaction, items: List[DesiredIngestion]
    ):
        Neo4jIngestionStrategy.ingest(transaction, items)


class GenericNeo4jWriter(TransactionalNeo4jWriter):
    def __init__(self, driver, database_name, query):
        super().__init__(driver, database_name)
        self.query = query

    def write_with_transaction(self, transaction: Transaction, items):
        for item in items:
            transaction.run(self.query, **item)


class TransactionlessNeo4jWriter(BaseNeo4jWriter):
    def __init__(self, driver, database_name, query, timeout=1800):
        super().__init__(driver, database_name)
        self.query_string = query
        self.timeout = timeout

    def make_query(self):
        return Query(self.query_string, timeout=self.timeout)

    def batch_write(self, items):
        with self.session() as session:
            for item in items:
                session.run(self.make_query(), **item)
