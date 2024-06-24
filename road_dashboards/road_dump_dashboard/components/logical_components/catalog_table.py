import base64
import json

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, callback, dash_table, html, no_update
from road_database_toolkit.dynamo_db.db_manager import DBManager

from road_dashboards.road_dump_dashboard.components.constants.components_ids import (
    DUMP_CATALOG,
    LOAD_NETS_DATA_NOTIFICATION,
    TABLES,
    UPDATE_RUNS_BTN,
    URL,
)
from road_dashboards.road_dump_dashboard.components.dashboard_layout.layout_wrappers import (
    card_wrapper,
    loading_wrapper,
)
from road_dashboards.road_dump_dashboard.components.logical_components.tables_properties import Tables

run_eval_db_manager = DBManager(table_name="algoroad_dump_catalog", primary_key="dump_name")


def layout():
    catalog_data = pd.DataFrame(run_eval_db_manager.scan()).drop(["batches", "populations", "split_conditions"], axis=1)
    catalog_data["total_frames"] = catalog_data["total_frames"].apply(lambda x: sum(x.values()))
    catalog_data_dict = catalog_data.to_dict("records")
    layout = html.Div(
        card_wrapper(
            [
                dbc.Row(html.H2("Datasets Catalog", className="mb-5")),
                dbc.Row(
                    dash_table.DataTable(
                        id=DUMP_CATALOG,
                        columns=[
                            {"name": i, "id": i, "deletable": False, "selectable": True}
                            for i in ["dump_name", "use_case", "user", "total_frames", "last_change"]
                        ],
                        data=catalog_data_dict,
                        filter_action="native",
                        sort_action="native",
                        sort_mode="multi",
                        sort_by=[{"column_id": "last_change", "direction": "desc"}],
                        row_selectable="multi",
                        selected_rows=[],
                        page_action="native",
                        page_current=0,
                        page_size=20,
                        css=[{"selector": ".show-hide", "rule": "display: none"}],
                        style_cell={"textAlign": "left"},
                        style_header={
                            "background-color": "#4e4e50",
                            "fontWeight": "bold",
                            "color": "white",
                        },
                        style_data={
                            "backgroundColor": "white",
                            "color": "rgb(102, 102, 102)",
                        },
                        style_table={
                            "border": "1px solid rgb(230, 230, 230)",
                        },
                    )
                ),
                dbc.Row(
                    dbc.Col(dbc.Button("Choose Datasets to Explore", id=UPDATE_RUNS_BTN, className="bg-primary mt-5")),
                ),
                loading_wrapper(html.Div(id=LOAD_NETS_DATA_NOTIFICATION)),
            ]
        )
    )
    return layout


@callback(
    Output(TABLES, "data"),
    Output(LOAD_NETS_DATA_NOTIFICATION, "children"),
    Output(URL, "hash"),
    Input(UPDATE_RUNS_BTN, "n_clicks"),
    State(DUMP_CATALOG, "derived_virtual_data"),
    State(DUMP_CATALOG, "derived_virtual_selected_rows"),
)
def init_run(n_clicks, rows, derived_virtual_selected_rows):
    if not n_clicks or not derived_virtual_selected_rows:
        return no_update, no_update, no_update

    rows = parse_catalog_rows(rows, derived_virtual_selected_rows)
    dumps = init_tables(rows)
    notification = dbc.Alert("Datasets loaded successfully!", color="success", dismissable=True)

    dumps_list = list(rows["dump_name"])
    dump_list_hash = "#" + base64.b64encode(json.dumps(dumps_list).encode("utf-8")).decode("utf-8")
    return dumps, notification, dump_list_hash


def init_tables(rows):
    tables = Tables(
        rows["dump_name"],
        **{table: rows[table].tolist() for table in rows.columns if table.endswith("_table") and any(rows[table])},
    ).__dict__
    return tables


def parse_catalog_rows(rows, derived_virtual_selected_rows):
    rows = pd.DataFrame([rows[i] for i in derived_virtual_selected_rows])
    return rows
