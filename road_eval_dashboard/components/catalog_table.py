import pandas as pd
import dash_bootstrap_components as dbc
from dash import dash_table, html, Output, Input, State, no_update, callback
from threading import Thread
from queue import Queue

from road_database_toolkit.dynamo_db.db_manager import DBManager
from road_eval_dashboard.components.common_filters import ALL_FILTERS
from road_eval_dashboard.components.components_ids import (
    NETS,
    MD_COLUMNS_TO_TYPE,
    MD_COLUMNS_TO_DISTINCT_VALUES,
    UPDATE_RUNS_BTN,
    RUN_EVAL_CATALOG,
    MD_COLUMNS_OPTION,
    LOAD_NETS_DATA_NOTIFICATION,
    EFFECTIVE_SAMPLES_PER_BATCH,
    NET_ID_TO_FB_BEST_THRESH,
)
from road_eval_dashboard.components.layout_wrapper import loading_wrapper
from road_eval_dashboard.components.net_properties import Nets, Net
from road_eval_dashboard.components.queries_manager import (
    generate_base_query,
    generate_grab_index_hist_query,
    generate_fb_query,
)
from road_eval_dashboard.graphs.precision_recall_curve import calc_best_thresh
from road_database_toolkit.athena.athena_utils import query_athena
from maffe_bins.utils.color_prints import warning_print

run_eval_db_manager = DBManager(table_name="algoroad_run_eval")


def generate_catalog_layout():
    catalog_data = pd.DataFrame(run_eval_db_manager.scan()).drop("batches", axis=1)
    catalog_data_dict = catalog_data.to_dict("records")
    layout = html.Div(
        [
            dbc.Row(html.H2("Net Catalog", className="mb-5")),
            dbc.Row(
                dash_table.DataTable(
                    id=RUN_EVAL_CATALOG,
                    columns=[
                        {"name": i, "id": i, "deletable": False, "selectable": True}
                        for i in ["net", "checkpoint", "dataset", "population", "total_frames", "user", "last_change"]
                    ],
                    data=catalog_data_dict,
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    sort_by=[
                        {"column_id": "last_change", "direction": "desc"},
                        {"column_id": "dataset", "direction": "desc"},
                        {"column_id": "user", "direction": "desc"},
                    ],
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
                dbc.Col(dbc.Button("Choose Runs to Compare", id=UPDATE_RUNS_BTN, className="bg-primary mt-5")),
            ),
            loading_wrapper([html.Div(id=LOAD_NETS_DATA_NOTIFICATION)]),
        ]
    )
    return layout


@callback(
    Output(NETS, "data"),
    Output(MD_COLUMNS_TO_TYPE, "data"),
    Output(MD_COLUMNS_OPTION, "data"),
    Output(MD_COLUMNS_TO_DISTINCT_VALUES, "data"),
    Output(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    Output(NET_ID_TO_FB_BEST_THRESH, "data"),
    Output(LOAD_NETS_DATA_NOTIFICATION, "children"),
    Input(UPDATE_RUNS_BTN, "n_clicks"),
    State(RUN_EVAL_CATALOG, "derived_virtual_data"),
    State(RUN_EVAL_CATALOG, "derived_virtual_selected_rows"),
    background=True,
)
def init_run(n_clicks, rows, derived_virtual_selected_rows):
    if not n_clicks or not derived_virtual_selected_rows:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update

    nets = init_nets(rows, derived_virtual_selected_rows)

    q1, q2, q3 = Queue(), Queue(), Queue()
    Thread(target=wrapper, args=(generate_meta_data_dicts, nets, q1)).start()
    Thread(target=wrapper, args=(generate_effective_samples_per_batch, nets, q2)).start()
    Thread(target=wrapper, args=(get_best_fb_per_net, nets, q3)).start()

    md_columns_to_type, md_columns_options, md_columns_to_distinguish_values = q1.get()
    effective_samples_per_batch = q2.get()
    net_id_to_best_thresh = q3.get()

    notification = dbc.Alert("Nets data loaded successfully!", color="success", dismissable=True)
    return (
        nets,
        md_columns_to_type,
        md_columns_options,
        md_columns_to_distinguish_values,
        effective_samples_per_batch,
        net_id_to_best_thresh,
        notification,
    )


def wrapper(func, arg, queue):
    queue.put(func(arg))


def generate_meta_data_dicts(nets):
    md_columns_to_type = get_meta_data_columns(nets)
    distinct_dict = get_distinct_values_dict(nets, md_columns_to_type)

    md_columns_options = [{"label": col.replace("_", " ").title(), "value": col} for col in md_columns_to_type.keys()]
    md_columns_to_distinguish_values = {
        col: [{"label": val.strip(" "), "value": f"'{val.strip(' ')}'"} for val in val_list[0].strip("[]").split(",")]
        for col, val_list in distinct_dict.items()
    }

    return md_columns_to_type, md_columns_options, md_columns_to_distinguish_values


def generate_effective_samples_per_batch(nets):
    tables_lists = nets["frame_tables"]
    meta_data = nets["meta_data"]
    query = generate_grab_index_hist_query(tables_lists, meta_data, ALL_FILTERS)
    try:
        data, _ = query_athena(database="run_eval_db", query=query)
        effective_samples_per_batch = data.to_dict("records")[0]
        return effective_samples_per_batch
    except:
        warning_print(
            "It seems like you're working with old dataset. In order to enjoy the full capabilites of the dashboard please re-run the 'parquets_converter_cfg' and 'generate_meta_data_table' stages of the dump."
        )
        return {}


def init_nets(rows, derived_virtual_selected_rows):
    rows = [rows[i] for i in derived_virtual_selected_rows]
    nets = Nets(
        list(
            Net(
                row["net"],
                row["checkpoint"],
                row["population"],
                **{table: row[table] for table in row if table.endswith("table") and row[table]},
            ).__dict__
            for row in rows
        )
    ).__dict__
    return nets


def get_meta_data_columns(nets):
    query = f"SELECT * FROM {nets['meta_data']} LIMIT 1"
    data, _ = query_athena(database="run_eval_db", query=query)
    md_columns_to_type = dict(data.dtypes.apply(lambda x: x.name))
    return md_columns_to_type


def get_distinct_values_dict(nets, md_columns_to_type):
    distinct_select = ",".join(
        [
            f' array_agg(DISTINCT "{col}") AS "{col}" '
            for col in md_columns_to_type.keys()
            if md_columns_to_type[col] == "object"
        ]
    )
    tables_lists = nets["frame_tables"]
    meta_data = nets["meta_data"]
    base_query = generate_base_query(tables_lists, meta_data, only_meta_data=True)
    query = f"SELECT {distinct_select} FROM ({base_query})"
    data, _ = query_athena(database="run_eval_db", query=query)
    distinct_dict = data.to_dict("list")
    return distinct_dict


def get_best_fb_per_net(nets):
    if not nets["gt_tables"] or not nets["pred_tables"]:
        return None

    query = generate_fb_query(
        nets["gt_tables"],
        nets["pred_tables"],
        nets["meta_data"],
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    data = data.fillna(1)
    net_id_to_best_thresh = calc_best_thresh(data)
    return net_id_to_best_thresh
