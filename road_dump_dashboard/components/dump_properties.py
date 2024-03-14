from dataclasses import dataclass
from itertools import zip_longest


@dataclass
class Dumps:
    def __init__(self, dump_names, **kwargs):
        self.names = dump_names

        meta_data_tables = kwargs.get("meta_data_table", [])
        self.meta_data_tables = dict(zip_longest(dump_names, meta_data_tables))

        lm_meta_data_tables = kwargs.get("lm_meta_data_table", [])
        self.lm_meta_data_tables = dict(zip_longest(dump_names, lm_meta_data_tables))

        re_meta_data_tables = kwargs.get("re_meta_data_table", [])
        self.re_meta_data_tables = dict(zip_longest(dump_names, re_meta_data_tables))

        pw_meta_data_tables = kwargs.get("pw_meta_data_table", [])
        self.pw_meta_data_tables = dict(zip_longest(dump_names, pw_meta_data_tables))

        self.tables = {
            "meta_data": self.meta_data_tables,
            "lm_meta_data": self.lm_meta_data_tables,
            "re_meta_data": self.re_meta_data_tables,
            "pw_meta_data": self.pw_meta_data_tables,
        }
