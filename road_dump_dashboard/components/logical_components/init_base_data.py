import pandas as pd
from road_database_toolkit.dynamo_db.db_manager import DBManager

from road_dump_dashboard.components.logical_components.tables_properties import Tables


run_eval_db_manager = DBManager(table_name="algoroad_dump_catalog", primary_key="dump_name")


def init_tables(rows):
    tables = Tables(
        rows["dump_name"],
        **{table: rows[table].tolist() for table in rows.columns if table.endswith("_table") and any(rows[table])},
    ).__dict__
    return tables


def parse_catalog_rows(rows, derived_virtual_selected_rows):
    rows = pd.DataFrame([rows[i] for i in derived_virtual_selected_rows])
    return rows
