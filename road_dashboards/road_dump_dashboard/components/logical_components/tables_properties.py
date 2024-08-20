import base64
import pickle as pkl
from dataclasses import dataclass, field
from itertools import zip_longest
from queue import Queue
from threading import Thread
from typing import Any, Dict, List

from dash import page_registry
from road_database_toolkit.athena.athena_utils import query_athena

from road_dashboards.road_dump_dashboard.components.constants.columns_properties import (
    BASE_COLUMNS,
    ArrayColumn,
    BaseColumn,
)

POSITION_COLUMNS = {
    "half_width",
    "pos",
    "pos_x",
    "pos_z",
    "ds_y_off",
    "de_y_off",
    "dp_points",
    "dv_dp_points",
    "dashed_start_y",
    "dashed_end_y",
}

THREE_DAYS = 60 * 24 * 3


@dataclass
class Table:
    name: str
    tables_dict: dict
    columns: Dict[str, BaseColumn] = field(default_factory=dict)

    def get_column_names(self, exclude_columns=List[str]):
        return [col for col in self.columns.values() if col.name not in exclude_columns]


class Tables:
    POTENTIAL_TABLES = ["meta_data", "lm_meta_data", "re_meta_data", "pw_meta_data", "rpw_meta_data"]

    def __init__(self, dump_names, **kwargs):
        self.names = dump_names
        self.meta_data, self.lm_meta_data, self.re_meta_data, self.pw_meta_data, self.rpw_meta_data = self.init_tables(
            dump_names, **kwargs
        )

    @staticmethod
    def get_tables_from_type(tables_type, num_of_dumps, **kwargs):
        tables = kwargs.get(f"{tables_type}_table", [""] * num_of_dumps)
        tables = [table if table else "" for table in tables]
        return tables

    def init_tables(self, dump_names, **kwargs):
        num_of_dumps = len(kwargs.get("meta_data_table"))
        tables_list = [
            self.get_tables_from_type(table_type, num_of_dumps, **kwargs) for table_type in self.POTENTIAL_TABLES
        ]
        queues = [Queue() for _ in self.POTENTIAL_TABLES]
        [
            Thread(target=wrapper, args=(generate_table_instance, queue, table_type, tables, dump_names)).start()
            for queue, table_type, tables in zip(queues, self.POTENTIAL_TABLES, tables_list)
        ]
        table_instances = [queue.get() for queue in queues]
        return table_instances


def wrapper(func, queue, *args):
    queue.put(func(*args))


def generate_table_instance(name, tables, dump_names):
    table = tables[0]
    tables_dict = dict(zip_longest(dump_names, tables))
    if not table:
        return Table(name, tables_dict)

    columns = get_table_columns(table)
    table_data = Table(name=name, tables_dict=tables_dict, columns=columns)
    return table_data


def get_table_columns(table):
    uninteresting_columns = ["pred_name", "dump_name", "population", "attributes"]

    query = f"SELECT * FROM ({table}) LIMIT 1"
    data, _ = query_athena(database="run_eval_db", query=query, cache_duration_minutes=THREE_DAYS)
    data = data.drop(columns=uninteresting_columns, errors="ignore", axis=1)

    existing_columns = data.columns.str.lower()
    dtypes = list(data.dtypes.apply(lambda x: x.name))
    drawables = [bool(col in POSITION_COLUMNS) for col in existing_columns]

    obj_cols = [
        col for col, dtype in zip(existing_columns, dtypes) if (dtype == "object") and (col not in POSITION_COLUMNS)
    ]
    distinct_dict = generate_distinct_dict(table, obj_cols)
    columns = {
        name: (
            ArrayColumn(name=name, dtype=dtype, distinct_values=distinct_dict.get(name, []), drawable=drawable)
            if drawables
            else BaseColumn(name=name, dtype=dtype, distinct_values=distinct_dict.get(name, []), drawable=drawable)
        )
        for name, dtype, drawable in zip(existing_columns, dtypes, drawables)
    }
    return columns


def generate_distinct_dict(table, columns_list):
    distinct_dict = get_distinct_values_dict(table, columns_list)
    parsed_distinct_dict = parse_distinct_dict(distinct_dict)
    return parsed_distinct_dict


def get_distinct_values_dict(table, columns_data_types_list, max_distinct_values=20):
    if not columns_data_types_list:
        return {}

    distinct_select = ",".join(
        [
            f' slice(array_agg(DISTINCT "{col}"), 1, {max_distinct_values}) AS "{col}" '
            for col in columns_data_types_list
        ]
    )
    query = f"SELECT {distinct_select} FROM {table}"
    data, _ = query_athena(database="run_eval_db", query=query, cache_duration_minutes=THREE_DAYS)
    distinct_dict = data.to_dict("list")
    return distinct_dict


def parse_distinct_dict(distinct_dict):
    columns_to_distinguish_values = {
        col: {f"'{val.strip(' ')}'": val.strip(" ") for val in val_list[0].strip("[]").split(",")}
        for col, val_list in distinct_dict.items()
    }
    return columns_to_distinguish_values


def get_tables_columns_union(main_tables: Table, meta_data_tables: Table = None):
    columns = main_tables.columns | (meta_data_tables.columns if meta_data_tables else {})
    return columns.values()


def get_columns_dict(main_tables: Table, meta_data_tables=None):
    columns = get_tables_columns_union(main_tables, meta_data_tables)
    columns_dict = {col.name: col.title() for col in columns if col.drawable is False}
    return columns_dict


def get_existing_column(name: str, main_tables: Table, meta_data_tables: Table = None):
    val = main_tables.columns.get(name)
    if val is None and meta_data_tables is not None:
        val = meta_data_tables.columns.get(name)

    return val


def get_curr_page_tables(tables: str, pathname: str) -> tuple[Table, Table]:
    tables = load_object(tables)
    page_properties = page_registry[f"pages.{pathname.strip('/')}"]
    main_table_name = page_properties["main_table"]
    meta_data_table_name = page_properties["meta_data_table"]
    main_tables = getattr(tables, main_table_name)
    meta_data_tables = getattr(tables, meta_data_table_name) if meta_data_table_name else None
    return main_tables, meta_data_tables


def dump_object(obj: Any) -> str:
    return base64.b64encode(pkl.dumps(obj)).decode("utf-8")


def load_object(dump_obj: str) -> Any:
    return pkl.loads(base64.b64decode(dump_obj))
