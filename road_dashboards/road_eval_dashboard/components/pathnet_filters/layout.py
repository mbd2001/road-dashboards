import dash_bootstrap_components as dbc
from dash import dcc, html

import road_dashboards.road_eval_dashboard.components.pathnet_filters.callbacks  # LOAD CALLBACKS - DO-NOT REMOVE!
from road_dashboards.road_eval_dashboard.components.common_filters import PATHNET_MD_FILTERS
from road_dashboards.road_eval_dashboard.components.components_ids import (
    BIN_POPULATION_DROPDOWN,
    PATHNET_FILTERS_IN_DROPDOWN,
    PATHNET_FILTERS_OUT_DROPDOWN,
    PATHNET_MD_FILTERS_SUBMIT_BUTTON,
    ROLE_POPULATION_VALUE,
    SPLIT_ROLE_POPULATION_DROPDOWN,
)
from road_dashboards.road_eval_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper
from road_dashboards.road_eval_dashboard.utils.url_state_utils import create_dropdown_options_list

BASIC_OPERATIONS = create_dropdown_options_list(
    labels=["Greater", "Greater or equal", "Less", "Less or equal", "Equal", "Not Equal", "Is NULL", "Is not NULL"],
    values=[">", ">=", "<", "<=", "=", "<>", "IS NULL", "IS NOT NULL"],
)


def get_pathnet_md_filters_rows():
    pathnet_md_filters_options = create_dropdown_options_list(
        labels=PATHNET_MD_FILTERS.keys(), values=PATHNET_MD_FILTERS.values(), do_hover=True
    )
    return [
        dbc.Row(
            dbc.Col(html.H3("Filter by Scene", className="mb-5"), width=5),
            style={"margin-bottom": "10px"},
        ),
        dbc.Row(
            dbc.Col(
                dcc.Dropdown(
                    id=PATHNET_FILTERS_IN_DROPDOWN,
                    options=pathnet_md_filters_options,
                    placeholder="Select Filters-in",
                    searchable=True,
                    multi=True,
                ),
            ),
            style={"margin-bottom": "10px"},
        ),
        dbc.Row(
            dbc.Col(
                dcc.Dropdown(
                    id=PATHNET_FILTERS_OUT_DROPDOWN,
                    options=pathnet_md_filters_options,
                    placeholder="Select Filters-out",
                    searchable=True,
                    multi=True,
                ),
            ),
            style={"margin-bottom": "10px"},
        ),
        dbc.Row(
            dbc.Col(dbc.Button("Update filters", id=PATHNET_MD_FILTERS_SUBMIT_BUTTON, color="success")),
            style={"margin-bottom": "10px"},
        ),
    ]


def get_pathnet_roles_filters_col():
    return [
        dbc.Row(
            [
                dbc.Col(html.H3("Filter by Split-Roles", className="mb-5"), width=5),
            ],
            style={"margin-bottom": "10px"},
        ),
        dbc.Row(
            [dbc.Col(loading_wrapper(dcc.Dropdown(id=BIN_POPULATION_DROPDOWN, value="")), width=4)],
            style={"margin-bottom": "10px"},
        ),
        dbc.Row(
            [
                dbc.Col(loading_wrapper(dcc.Dropdown(id=SPLIT_ROLE_POPULATION_DROPDOWN, value="")), width=4),
                dbc.Col(
                    loading_wrapper(dcc.Dropdown(id="roles_operation", options=BASIC_OPERATIONS, value="")),
                    width=4,
                ),
                dbc.Col(loading_wrapper(dcc.Dropdown(id=ROLE_POPULATION_VALUE, value="")), width=4),
            ],
            style={"margin-bottom": "10px"},
        ),
        dbc.Row(
            [dbc.Col(dbc.Button("Update filters", id="pathnet_update_filters_btn", color="success"))],
            style={"margin-bottom": "10px"},
        ),
    ]


def create_pathnet_filters_layout():
    pathnet_md_filters_rows = get_pathnet_md_filters_rows()
    pathnet_roles_filters_col = get_pathnet_roles_filters_col()
    filters_layout = card_wrapper(
        dbc.Row(
            [
                dbc.Col(pathnet_md_filters_rows, width=5),
                dbc.Col(pathnet_roles_filters_col, width=7),
            ],
            style={"margin-bottom": "10px"},
        )
    )
    return filters_layout


layout = create_pathnet_filters_layout()
