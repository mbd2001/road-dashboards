from dataclasses import dataclass
from itertools import zip_longest


@dataclass
class Dumps:
    def __init__(self, dump_names, **kwargs):
        self.names = dump_names

        general_md_tables = kwargs.get("meta_data_table", [])
        general_md_tables = dict(zip_longest(dump_names, general_md_tables))

        lm_meta_data_tables = kwargs.get("lm_meta_data_table", [])
        self.lm_meta_data_tables = self.generate_data_tables(dump_names, lm_meta_data_tables, general_md_tables)

        re_meta_data_tables = kwargs.get("re_meta_data_table", [])
        self.re_meta_data_tables = self.generate_data_tables(dump_names, re_meta_data_tables, general_md_tables)

        pw_meta_data_tables = kwargs.get("pw_meta_data_table", [])
        self.pw_meta_data_tables = self.generate_data_tables(dump_names, pw_meta_data_tables, general_md_tables)

        self.meta_data_tables = self.parse_general_meta_data_table(general_md_tables)

        self.tables = {
            "meta_data": self.meta_data_tables,
            "lm_meta_data": self.lm_meta_data_tables,
            "re_meta_data": self.re_meta_data_tables,
            "pw_meta_data": self.pw_meta_data_tables,
        }

    @staticmethod
    def generate_data_tables(dump_names, specific_tables, general_md_tables):
        dump_to_original_table = dict(zip_longest(dump_names, specific_tables))
        final_data_tables_dict = {
            name: f"SELECT A.* FROM {dump_to_original_table[name]} A LEFT JOIN {general_md_tables[name]} B ON ((A.clip_name = B.clip_name) AND (A.grabIndex = B.grabIndex))"
            for name in dump_names
        }
        return final_data_tables_dict

    @staticmethod
    def parse_general_meta_data_table(general_md_tables):
        meta_data_tables = {
            dump_name: f"SELECT * FROM {meta_data_table}" for dump_name, meta_data_table in general_md_tables.items()
        }
        return meta_data_tables
