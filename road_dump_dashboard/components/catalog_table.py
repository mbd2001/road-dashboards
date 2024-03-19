import base64
import json
import pandas as pd
import dash_bootstrap_components as dbc
from dash import dash_table, html, Output, Input, State, no_update, callback

from road_dump_dashboard.components.components_ids import (
    DUMPS,
    MD_COLUMNS_TO_TYPE,
    MD_COLUMNS_TO_DISTINCT_VALUES,
    UPDATE_RUNS_BTN,
    DUMP_CATALOG,
    MD_COLUMNS_OPTION,
    LOAD_NETS_DATA_NOTIFICATION, URL,
)
from road_dump_dashboard.components.init_base_data import parse_catalog_rows, init_dumps, generate_meta_data_dicts, \
    run_eval_db_manager
from road_dump_dashboard.components.layout_wrapper import loading_wrapper


def generate_catalog_layout():
    catalog_data = pd.DataFrame(run_eval_db_manager.scan()).drop(["batches", "populations"], axis=1)
    catalog_data["total_frames"] = catalog_data["total_frames"].apply(lambda x: sum(x.values()))
    catalog_data_dict = catalog_data.to_dict("records")
    layout = html.Div(
        [
            dbc.Row(html.H2("Dump Catalog", className="mb-5")),
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
                dbc.Col(dbc.Button("Choose Dump to Explore", id=UPDATE_RUNS_BTN, className="bg-primary mt-5")),
            ),
            loading_wrapper([html.Div(id=LOAD_NETS_DATA_NOTIFICATION)]),
        ]
    )
    return layout


@callback(
    Output(DUMPS, "data"),
    Output(MD_COLUMNS_TO_TYPE, "data"),
    Output(MD_COLUMNS_OPTION, "data"),
    Output(MD_COLUMNS_TO_DISTINCT_VALUES, "data"),
    Output(LOAD_NETS_DATA_NOTIFICATION, "children"),
    Output(URL, "hash"),
    Input(UPDATE_RUNS_BTN, "n_clicks"),
    State(DUMP_CATALOG, "derived_virtual_data"),
    State(DUMP_CATALOG, "derived_virtual_selected_rows"),
    background=True,
)
def init_run(n_clicks, rows, derived_virtual_selected_rows):
    if not n_clicks or not derived_virtual_selected_rows:
        return no_update, no_update, no_update, no_update, no_update, no_update

    rows = parse_catalog_rows(rows, derived_virtual_selected_rows)
    dumps = init_dumps(rows)
    md_columns_to_type, md_columns_options, md_columns_to_distinguish_values = generate_meta_data_dicts(
        list(dumps["meta_data_tables"].values())[0]
    )

    notification = dbc.Alert("Dump data loaded successfully!", color="success", dismissable=True)

    dumps_list = list(rows["dump_name"])
    dump_list_hash = "#" + base64.b64encode(json.dumps(dumps_list).encode("utf-8")).decode("utf-8")
    return (
        dumps,
        md_columns_to_type,
        md_columns_options,
        md_columns_to_distinguish_values,
        notification,
        dump_list_hash,
    )
