from dataclasses import dataclass
from itertools import zip_longest


@dataclass
class Dumps:
    def __init__(self, dump_names, **kwargs):
        self.names = dump_names

        test_tables = kwargs.get("test_table", [])
        self.test_tables = dict(zip_longest(dump_names, test_tables))

        train_tables = kwargs.get("train_table", [])
        self.train_tables = dict(zip_longest(dump_names, train_tables))

        given_all_tables = kwargs.get("all_table", [])
        self.all_tables = self.compute_all_tables(test_tables, train_tables, given_all_tables, dump_names)

        self.tables = {
            "all": self.all_tables,
            "test": self.test_tables,
            "train": self.train_tables,
        }

    @staticmethod
    def compute_all_tables(test_tables, train_tables, given_all_tables, dump_names):
        nominated_all_tables = [
            f"(SELECT * FROM {' UNION SELECT * FROM '.join([table for table in [test_table, train_table] if table])})"
            for test_table, train_table in zip_longest(test_tables, train_tables)
        ]

        all_tables = [
            given_all_table or nominated_all_table
            for given_all_table, nominated_all_table in zip_longest(given_all_tables, nominated_all_tables)
        ]
        return dict(zip(dump_names, all_tables))
