import base64
import pickle as pkl
from dataclasses import dataclass
from itertools import zip_longest
from queue import Queue
from threading import Thread
from typing import Any, Dict, Iterable, List

from road_database_toolkit.athena.athena_utils import get_table, query_athena

from road_dashboards.road_dump_dashboard.components.constants.columns_properties import (
    ArrayColumn,
    BoolColumn,
    Column,
    NumericColumn,
    StringColumn,
)

POTENTIAL_TABLES = ["meta_data", "lm_meta_data", "rpw_meta_data"]

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
DTYPE_TO_COLUMN = {
    "int": NumericColumn,
    "float": NumericColumn,
    "double": NumericColumn,
    "boolean": BoolColumn,
    "string": StringColumn,
}


@dataclass
class Table:
    dataset_name: str
    table_name: str

    def __bool__(self):
        return bool(self.table_name)


@dataclass
class TableType:
    tables: List[Table]
    columns: Dict[str, Column]

    def get_column_names(self, exclude_columns=List[str]):
        return [col for col in self.columns.values() if col.name not in exclude_columns]

    def __bool__(self):
        return any(self.tables)


def init_tables(dump_names: List[str], **kwargs):
    num_of_dumps = len(kwargs.get("meta_data_table"))
    tables_list = [get_tables_from_type(table_type, num_of_dumps, **kwargs) for table_type in POTENTIAL_TABLES]
    queues = [Queue() for _ in POTENTIAL_TABLES]
    [
        Thread(target=wrapper, args=(generate_table_instance, queue, tables, dump_names)).start()
        for queue, table_type, tables in zip(queues, POTENTIAL_TABLES, tables_list)
    ]
    table_instances = [queue.get() for queue in queues]
    return table_instances


def get_tables_from_type(tables_type, num_of_dumps, **kwargs):
    tables = kwargs.get(f"{tables_type}_table", [""] * num_of_dumps)
    tables = [table if table else "" for table in tables]
    return tables


def wrapper(func, queue, *args):
    queue.put(func(*args))


def generate_table_instance(tables, dump_names):
    table = tables[0]
    tables_dict = [
        Table(dataset_name=dump_name, table_name=table) for dump_name, table in zip_longest(dump_names, tables)
    ]
    if not table:
        return TableType(tables=tables_dict, columns={})

    columns = get_table_columns(table)
    table_data = TableType(tables=tables_dict, columns=columns)
    return table_data


def get_table_columns(table):
    uninteresting_columns = ["pred_name", "dump_name", "population", "attributes"]

    existing_table = get_table(table_name=table, database="run_eval_db")
    existing_columns = existing_table["Table"]["StorageDescriptor"]["Columns"]
    existing_columns = [column for column in existing_columns if column["Name"] not in uninteresting_columns]

    obj_cols = [
        column["Name"]
        for column in existing_table["Table"]["StorageDescriptor"]["Columns"]
        if column["Type"] == "string"
    ]
    distinct_dict = generate_distinct_dict(table, obj_cols)
    columns = {
        column["Name"]: DTYPE_TO_COLUMN.get(column["Type"], ArrayColumn)(
            name=column["Name"], distinct_values=distinct_dict.get(column["Name"], [])
        )
        for column in existing_columns
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
        col: [val.strip(" ") for val in val_list[0].strip("[]").split(",")] for col, val_list in distinct_dict.items()
    }
    return columns_to_distinguish_values


def get_tables_columns_union(main_tables: TableType, meta_data_tables: TableType = None) -> Iterable[Column]:
    columns = main_tables.columns | (meta_data_tables.columns if meta_data_tables else {})
    return columns.values()


def get_columns_dict(main_tables: TableType, meta_data_tables=None) -> Dict[str, str]:
    columns = get_tables_columns_union(main_tables, meta_data_tables)
    columns_dict = {col.name: col.title() for col in columns if not isinstance(col, ArrayColumn)}
    return columns_dict


def get_existing_column(name: str, main_tables: TableType, meta_data_tables: TableType = None) -> Column:
    val = main_tables.columns.get(name)
    if val is None and meta_data_tables is not None:
        val = meta_data_tables.columns.get(name)

    return val


def dump_object(obj: Any) -> str:
    return base64.b64encode(pkl.dumps(obj)).decode("utf-8")


def load_object(dump_obj: str) -> Any:
    return pkl.loads(base64.b64decode(dump_obj))
