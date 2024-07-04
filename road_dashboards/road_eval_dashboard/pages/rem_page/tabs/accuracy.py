import dash_bootstrap_components as dbc
from dash import Input, Output, callback, no_update
from road_database_toolkit.athena.athena_utils import query_athena

from road_dashboards.road_eval_dashboard.components.components_ids import (
    MD_FILTERS,
    NETS,
    REM_ACCURACY_ERROR_THRESHOLD_SLIDER,
    REM_OVERALL_ACCURATE,
    REM_ROLES_DROPDOWN,
    REM_SOURCE_DROPDOWN,
)
from road_dashboards.road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_dashboards.road_eval_dashboard.components.layout_wrapper import card_wrapper
from road_dashboards.road_eval_dashboard.components.queries_manager import generate_overall_stats_query
from road_dashboards.road_eval_dashboard.graphs.meta_data_filters_graph import draw_meta_data_filters
from road_dashboards.road_eval_dashboard.pages.rem_page.tabs.accuracy_utils import get_accuracy_layout
from road_dashboards.road_eval_dashboard.pages.rem_page.utils import REM_TYPE, get_rem_score

TAB = "accuracy"


def get_overall_layout():
    return card_wrapper(
        [
            dbc.Row(graph_wrapper(REM_OVERALL_ACCURATE)),
        ]
    )


layout = get_accuracy_layout(TAB, extra_layout_after_setting=get_overall_layout())


@callback(
    Output(REM_OVERALL_ACCURATE, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
    Input(REM_ROLES_DROPDOWN, "value"),
    Input({"rem_type": REM_TYPE, "out": REM_SOURCE_DROPDOWN}, "value"),
    Input({"rem_type": REM_TYPE, "out": REM_ACCURACY_ERROR_THRESHOLD_SLIDER, "tab": TAB}, "value"),
)
def get_frame_count(meta_data_filters, nets, role, Z_source, threshold):
    if not nets:
        return no_update

    label = f"rem_{TAB}_error_{Z_source}"
    query = generate_overall_stats_query(
        nets["gt_tables"],
        nets["meta_data"],
        label_col=label,
        ignore_value=-3,
        unavailable_value=-1,
        threshold=threshold,
        role=role,
        meta_data_filters=meta_data_filters,
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    return draw_meta_data_filters(
        data,
        ["accurate", "inaccurate", "unavailable", "ignore"],
        get_rem_score,
        title=f"Overall Stats",
        xaxis="Status",
        yaxis="Percentage",
        hover=True,
    )
