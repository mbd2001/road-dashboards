import dash_bootstrap_components as dbc
import dash_daq as daq

from road_eval_dashboard.components.common_filters import (
    CURVE_BY_DIST_FILTERS,
    CURVE_BY_RAD_FILTERS,
    EVENT_FILTERS,
    LANE_MARK_TYPE_FILTERS,
    ROAD_TYPE_FILTERS,
    WEATHER_FILTERS,
)
from road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_eval_dashboard.components.layout_wrapper import card_wrapper
from road_eval_dashboard.components.queries_manager import (
    generate_compare_metric_query,
    run_query_with_nets_names_processing,
)
from road_eval_dashboard.road_eval_dashboard.graphs import draw_meta_data_filters

Z_BINS = list(range(0, 300, 50)) + [999]
Z_FILTERS = {f"{z}": f"rem_point_Z BETWEEN {z} AND {Z_BINS[i+1]}" for i, z in enumerate(Z_BINS[:-1])}
SEC_BINS = [r * 0.5 for r in range(0, 11)] + [999]
SEC_FILTERS = {f"{sec}": f"rem_point_sec BETWEEN {sec} AND {SEC_BINS[i+1]}" for i, sec in enumerate(SEC_BINS[:-1])}
REM_TYPE = "rem"
REM_FILTERS = {
    "Z": {"filters": Z_FILTERS},
    "sec": {"filters": SEC_FILTERS},
    "road_type": {"filters": ROAD_TYPE_FILTERS},
    "lane_mark_type": {"filters": LANE_MARK_TYPE_FILTERS},
    "event": {"filters": EVENT_FILTERS},
    "weather": {"filters": WEATHER_FILTERS},
    "curve": {"filters": CURVE_BY_RAD_FILTERS, "dist_filters": CURVE_BY_DIST_FILTERS, "sort_by_dist": True},
}
IGNORES_FILTER = "{col} != -1 AND {col} < 999"


def get_base_graph_layout(filter_name, tab, sort_by_dist=False):
    layout = card_wrapper(
        [
            dbc.Row(
                graph_wrapper(
                    {
                        "out": "graph",
                        "filter": filter_name,
                        "rem_type": REM_TYPE,
                        "sort_by_dist": sort_by_dist,
                        "tab": tab,
                    }
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
    role="",
):
    query = generate_compare_metric_query(
        nets["gt_tables"],
        nets["meta_data"],
        label,
        pred,
        interesting_filters,
        meta_data_filters=meta_data_filters,
        extra_filters=IGNORES_FILTER.format(col=label),
        compare_operator=compare_operator,
        extra_columns=["rem_point_sec", "rem_point_Z"],
        role=role,
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
