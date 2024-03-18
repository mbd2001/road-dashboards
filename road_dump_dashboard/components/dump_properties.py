from dataclasses import dataclass
from itertools import zip_longest


@dataclass
class Dumps:
    def __init__(self, dump_names, **kwargs):
        self.names = dump_names

        meta_data_tables = kwargs.get("meta_data_table", [])
        self.meta_data_tables = dict(zip_longest(dump_names, meta_data_tables))

        lm_meta_data_tables = kwargs.get("lm_meta_data_table", [])
        self.lm_meta_data_tables = self.generate_data_tables(lm_meta_data_tables)

        re_meta_data_tables = kwargs.get("re_meta_data_table", [])
        self.re_meta_data_tables = self.generate_data_tables(re_meta_data_tables)

        pw_meta_data_tables = kwargs.get("pw_meta_data_table", [])
        self.pw_meta_data_tables = self.generate_data_tables(pw_meta_data_tables)

        self.tables = {  # TODO: parse meta_data more elegantly
            "meta_data": {
                dump_name: f"SELECT * FROM {meta_data_table} WHERE TRUE"
                for dump_name, meta_data_table in self.meta_data_tables.items()
            },
            "lm_meta_data": self.lm_meta_data_tables,
            "re_meta_data": self.re_meta_data_tables,
            "pw_meta_data": self.pw_meta_data_tables,
        }

    def generate_data_tables(self, original_tables):
        dump_to_original_table = dict(zip_longest(self.names, original_tables))
        final_data_tables_dict = {
            name: f"SELECT A.* FROM {dump_to_original_table[name]} A LEFT JOIN {self.meta_data_tables[name]} B ON ((A.clip_name = B.clip_name) AND (A.grabIndex = B.grabIndex)) WHERE TRUE"
            for name in self.names
        }
        print(final_data_tables_dict)
        return final_data_tables_dict
