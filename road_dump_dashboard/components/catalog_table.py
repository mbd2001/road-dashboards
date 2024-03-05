import pandas as pd
import dash_bootstrap_components as dbc
from dash import dash_table, html, Output, Input, State, no_update, callback

from road_database_toolkit.dynamo_db.db_manager import DBManager
from road_dump_dashboard.components.components_ids import (
    POPULATION_TABLES,
    MD_COLUMNS_TO_TYPE,
    MD_COLUMNS_TO_DISTINCT_VALUES,
    UPDATE_RUNS_BTN,
    DUMP_CATALOG,
    MD_COLUMNS_OPTION,
    LOAD_NETS_DATA_NOTIFICATION,
)
from road_dump_dashboard.components.layout_wrapper import loading_wrapper
from road_database_toolkit.athena.athena_utils import query_athena

run_eval_db_manager = DBManager(table_name="algoroad_dump_catalog")


def generate_catalog_layout():
    catalog_data = pd.DataFrame(run_eval_db_manager.scan()).drop(["batches", "populations", "total_frames"], axis=1)
    catalog_data_dict = catalog_data.to_dict("records")
    layout = html.Div(
        [
            dbc.Row(html.H2("Dump Catalog", className="mb-5")),
            dbc.Row(
                dash_table.DataTable(
                    id=DUMP_CATALOG,
                    columns=[
                        {"name": i, "id": i, "deletable": False, "selectable": True}
                        for i in ["dump_name", "use_case", "user", "last_change"]
                    ],
                    data=catalog_data_dict,
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    sort_by=[
                        {"column_id": "user", "direction": "desc"},
                        {"column_id": "last_change", "direction": "desc"},
                    ],
                    row_selectable="single",
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
    Output(POPULATION_TABLES, "data"),
    Output(MD_COLUMNS_TO_TYPE, "data"),
    Output(MD_COLUMNS_OPTION, "data"),
    Output(MD_COLUMNS_TO_DISTINCT_VALUES, "data"),
    Output(LOAD_NETS_DATA_NOTIFICATION, "children"),
    Input(UPDATE_RUNS_BTN, "n_clicks"),
    State(DUMP_CATALOG, "derived_virtual_data"),
    State(DUMP_CATALOG, "derived_virtual_selected_rows"),
    background=True,
)
def init_run(n_clicks, rows, derived_virtual_selected_rows):
    if not n_clicks or not derived_virtual_selected_rows:
        return no_update, no_update, no_update, no_update, no_update

    row = rows[derived_virtual_selected_rows[0]]
    population_tables = {
        get_population_name(table): row[table] for table in row.keys() if table.endswith("_table") and any(row[table])
    }

    population_tables["All"] = f"(SELECT * FROM {'UNION SELECT * FROM'.join(population_tables.values())})"
    md_columns_to_type, md_columns_options, md_columns_to_distinguish_values = generate_meta_data_dicts(
        population_tables["All"]
    )

    notification = dbc.Alert("Dump data loaded successfully!", color="success", dismissable=True)
    return (
        population_tables,
        md_columns_to_type,
        md_columns_options,
        md_columns_to_distinguish_values,
        notification,
    )


def get_population_name(table_name):
    return "Test" if "test" in table_name else "Train"


def generate_meta_data_dicts(population_tables):
    md_columns_to_type = get_meta_data_columns(population_tables)
    distinct_dict = get_distinct_values_dict(population_tables, md_columns_to_type)

    md_columns_options = [{"label": col.replace("_", " ").title(), "value": col} for col in md_columns_to_type.keys()]
    md_columns_to_distinguish_values = {
        col: [{"label": val.strip(" "), "value": f"'{val.strip(' ')}'"} for val in val_list[0].strip("[]").split(",")]
        for col, val_list in distinct_dict.items()
    }

    return md_columns_to_type, md_columns_options, md_columns_to_distinguish_values


def get_meta_data_columns(md_table):
    query = f"SELECT * FROM {md_table} LIMIT 1"
    data, _ = query_athena(database="run_eval_db", query=query)
    md_columns_to_type = dict(data.dtypes.apply(lambda x: x.name))
    return md_columns_to_type


def get_distinct_values_dict(population_tables, md_columns_to_type):
    distinct_select = ",".join(
        [
            f' array_agg(DISTINCT "{col}") AS "{col}" '
            for col in md_columns_to_type.keys()
            if md_columns_to_type[col] == "object"
        ]
    )
    query = f"SELECT {distinct_select} FROM {population_tables}"
    data, _ = query_athena(database="run_eval_db", query=query)
    distinct_dict = data.to_dict("list")
    return distinct_dict
