import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import dcc

from road_eval_dashboard.components.common_filters import (
    CURVE_BY_DIST_FILTERS,
    CURVE_BY_RAD_FILTERS,
    EVENT_FILTERS,
    LANE_MARK_TYPE_FILTERS,
    ROAD_TYPE_FILTERS,
    WEATHER_FILTERS,
)
from road_eval_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper
from road_eval_dashboard.components.queries_manager import (
    generate_compare_metric_query,
    run_query_with_nets_names_processing,
)
from road_eval_dashboard.graphs.meta_data_filters_graph import draw_meta_data_filters

REM_TYPE = ""
REM_FILTERS = {
    "road_type": {"filters": ROAD_TYPE_FILTERS},
    "lane_mark_type": {"filters": LANE_MARK_TYPE_FILTERS},
    "event": {"filters": EVENT_FILTERS},
    "weather": {"filters": WEATHER_FILTERS},
    "curve": {"filters": CURVE_BY_RAD_FILTERS, "dist_filters": CURVE_BY_DIST_FILTERS, "sort_by_dist": True},
}


def get_base_graph_layout(filter_name, tab, sort_by_dist=False):
    layout = card_wrapper(
        [
            dbc.Row(
                loading_wrapper(
                    [
                        dcc.Graph(
                            id={
                                "out": "graph",
                                "filter": filter_name,
                                "rem_type": REM_TYPE,
                                "sort_by_dist": sort_by_dist,
                                "tab": tab,
                            },
                            config={"displayModeBar": False},
                        )
                    ]
                )
            ),
            dbc.Stack(
                (
                    [
                        daq.BooleanSwitch(
                            id={
                                "out": "sort_by_dist",
                                "filter": filter_name,
                                "rem_type": REM_TYPE,
                                "sort_by_dist": sort_by_dist,
                                "tab": tab,
                            },
                            on=False,
                            label="Sort By Dist",
                            labelPosition="top",
                            persistence=True,
                            persistence_type="session",
                        )
                    ]
                    if sort_by_dist
                    else []
                ),
                direction="horizontal",
                gap=3,
            ),
        ]
    )
    return layout


def get_rem_fig(
    meta_data_filters,
    nets,
    interesting_filters,
    effective_samples,
    filter_name,
    title,
    label,
    pred,
    compare_operator="<=",
):
    query = generate_compare_metric_query(
        nets["gt_tables"],
        nets["meta_data"],
        label,
        pred,
        interesting_filters,
        meta_data_filters=meta_data_filters,
        extra_filters=f"{label} != -1 AND {label} < 999",
        compare_operator=compare_operator,
        is_add_filters_count=True,
    )
    data, _ = run_query_with_nets_names_processing(query)
    filter_name_to_display = filter_name.replace("_", " ").capitalize()
    data = data.sort_values(by="net_id")
    fig = draw_meta_data_filters(
        data,
        list(interesting_filters.keys()),
        get_rem_score,
        effective_samples=effective_samples,
        title=f"{title} Per {filter_name_to_display}",
        yaxis="Score",
        hover=True,
    )
    return fig


def get_rem_score(row, filter):
    score = row[f"score_{filter}"]
    return score
