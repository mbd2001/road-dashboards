import base64
import json

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, callback, dash_table, html, no_update
from road_database_toolkit.dynamo_db.db_manager import DBManager

from road_dashboards.road_dump_dashboard.components.constants.components_ids import (
    COLUMN_SELECTOR,
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

dump_db_manager = DBManager(table_name="algoroad_dump_catalog", primary_key="dump_name")

table_columns = {
    "dump_name": "Dataset Name",
    "use_case": "Use Case",
    "user": "User",
    "total_frames": "Total Frames",
    "last_change": "Last Change",
    "hfov": "HFOV",
    "jira": "JIRA",
}
default_unchecked_columns = ["hfov", "jira"]


def get_column_selector():
    return dbc.DropdownMenu(
        label="Select Columns",
        children=[
            dbc.Checklist(
                options=table_columns,
                value=[col for col in table_columns if col not in default_unchecked_columns],
                id=COLUMN_SELECTOR,
                inline=False,
                className="dropdown-item",
                inputClassName="me-2",
            )
        ],
        right=True,
        color="secondary",
        style={"position": "absolute", "right": "10px", "top": "10px"},
    )


def get_data_table():
    catalog_data = pd.DataFrame(dump_db_manager.scan(), columns=table_columns.keys())
    catalog_data["total_frames"] = catalog_data["total_frames"].apply(lambda x: sum(x.values()))
    catalog_data_dict = catalog_data.to_dict("records")

    columns = [{"name": name, "id": col} for col, name in table_columns.items() if col not in default_unchecked_columns]

    return dash_table.DataTable(
        id=DUMP_CATALOG,
        columns=columns,
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


def layout():
    layout = html.Div(
        card_wrapper(
            [
                dbc.Row(html.H2("Datasets Catalog", className="mb-5")),
                dbc.Row(dbc.Col(get_column_selector(), width={"size": 12})),
                dbc.Row(get_data_table()),
                dbc.Row(
                    dbc.Col(dbc.Button("Choose Datasets to Explore", id=UPDATE_RUNS_BTN, className="bg-primary mt-5")),
                ),
                loading_wrapper(html.Div(id=LOAD_NETS_DATA_NOTIFICATION)),
            ]
        )
    )
    return layout


@callback(Output(DUMP_CATALOG, "columns"), Input(COLUMN_SELECTOR, "value"))
def update_columns(selected_columns):
    return [{"name": name, "id": col} for col, name in table_columns.items() if col in selected_columns]


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

    datasets_ids = parse_catalog_rows(rows, derived_virtual_selected_rows)["dump_name"]
    datasets = [dump_db_manager.get_item(dataset_id) for dataset_id in datasets_ids]
    datasets = pd.DataFrame(datasets)
    dumps = init_tables(datasets)

    notification = dbc.Alert("Datasets loaded successfully!", color="success", dismissable=True)

    dumps_list = list(datasets["dump_name"])
    dump_list_hash = "#" + base64.b64encode(json.dumps(dumps_list).encode("utf-8")).decode("utf-8")
    return dumps, notification, dump_list_hash


def init_tables(datasets):
    tables = Tables(
        datasets["dump_name"],
        **{
            table: datasets[table].tolist()
            for table in datasets.columns
            if table.endswith("_table") and any(datasets[table])
        },
    ).__dict__
    return tables


def parse_catalog_rows(rows, derived_virtual_selected_rows):
    rows = pd.DataFrame([rows[i] for i in derived_virtual_selected_rows])
    return rows
