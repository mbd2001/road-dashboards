import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import MATCH, Input, Output, State, callback, html, no_update, register_page

from road_dashboards.road_eval_dashboard.components import base_dataset_statistics, meta_data_filter
from road_dashboards.road_eval_dashboard.components.common_filters import (
    CURVE_BY_DIST_FILTERS,
    CURVE_BY_RAD_FILTERS,
    DIST_FROM_CURVE_VMAX_15_FILTERS,
    DIST_FROM_CURVE_VMAX_25_FILTERS,
    DIST_FROM_CURVE_VMAX_35_FILTERS,
    MAX_SPEED_FILTERS,
    VMAX_BINS_FILTERS,
)
from road_dashboards.road_eval_dashboard.components.components_ids import EFFECTIVE_SAMPLES_PER_BATCH, MD_FILTERS, NETS
from road_dashboards.road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_dashboards.road_eval_dashboard.components.layout_wrapper import card_wrapper
from road_dashboards.road_eval_dashboard.components.page_properties import PageProperties
from road_dashboards.road_eval_dashboard.components.queries_manager import (
    generate_vmax_fb_query,
    generate_vmax_success_rate_query,
    run_query_with_nets_names_processing,
)
from road_dashboards.road_eval_dashboard.graphs.meta_data_filters_graph import calc_fb_per_row, draw_meta_data_filters

f_beta = 1
B2 = f_beta**2


extra_properties = PageProperties("line-chart")
register_page(__name__, path="/max_speed", name="Max Speed", order=7, **extra_properties.__dict__)

MAX_SPEED_FILTERS = {
    "road_type": MAX_SPEED_FILTERS,
    "vmax_bins": VMAX_BINS_FILTERS,
    "dist_from_curve_35": DIST_FROM_CURVE_VMAX_35_FILTERS,
    "dist_from_curve_25": DIST_FROM_CURVE_VMAX_25_FILTERS,
    "dist_from_curve_15": DIST_FROM_CURVE_VMAX_15_FILTERS,
}
MAX_SPEED_DIST_FILTERS = {"curve": (CURVE_BY_DIST_FILTERS, CURVE_BY_RAD_FILTERS)}
VMAX_TYPE_KEY = "vmax"
VLIMIT_TYPE_KEY = "vlimit"
MAX_SPEED_TYPES = [VMAX_TYPE_KEY, VLIMIT_TYPE_KEY]


def get_filters_graphs():
    graphs = []
    for t in MAX_SPEED_TYPES:
        for filter_name in MAX_SPEED_FILTERS:
            graphs.append(get_base_graph_layout(filter_name, t))
        for filter_name in MAX_SPEED_DIST_FILTERS:
            graphs.append(get_base_graph_layout(filter_name, t, True))
    return graphs


def get_base_graph_layout(filter_name, max_speed_type, is_sort_by_dist=False):
    layout = card_wrapper(
        [
            dbc.Row(
                graph_wrapper(
                    {
                        "out": "graph",
                        "filter": filter_name,
                        "type": max_speed_type,
                        "is_sort_by_dist": is_sort_by_dist,
                    },
                )
            ),
            dbc.Stack(
                [
                    daq.BooleanSwitch(
                        id={
                            "out": "success_rate",
                            "filter": filter_name,
                            "type": max_speed_type,
                            "is_sort_by_dist": is_sort_by_dist,
                        },
                        on=False,
                        label="Fb <-> Success Rate",
                        labelPosition="top",
                    ),
                ]
                + (
                    [
                        daq.BooleanSwitch(
                            id={
                                "out": "sort_by_dist",
                                "filter": filter_name,
                                "type": max_speed_type,
                                "is_sort_by_dist": is_sort_by_dist,
                            },
                            on=False,
                            label="Sort By Dist",
                            labelPosition="top",
                        ),
                    ]
                    if is_sort_by_dist
                    else []
                ),
                direction="horizontal",
                gap=3,
            ),
        ]
    )
    return layout


layout = html.Div(
    [html.H1("Max Speed Metrics", className="mb-5"), meta_data_filter.layout, base_dataset_statistics.frame_layout]
    + get_filters_graphs()
)


@callback(
    Output({"out": "graph", "filter": MATCH, "type": MATCH, "is_sort_by_dist": False}, "figure"),
    Input(MD_FILTERS, "data"),
    Input({"out": "success_rate", "filter": MATCH, "type": MATCH, "is_sort_by_dist": False}, "on"),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    State({"out": "graph", "filter": MATCH, "type": MATCH, "is_sort_by_dist": False}, "id"),
)
def get_none_dist_graph(meta_data_filters, is_success_rate, nets, effective_samples, input_id):
    if not nets:
        return no_update
    filter_name = input_id["filter"]
    fig = get_fig_by_filter(
        effective_samples=effective_samples,
        filter_name=filter_name,
        interesting_filters=MAX_SPEED_FILTERS[filter_name],
        is_success_rate=is_success_rate,
        meta_data_filters=meta_data_filters,
        nets=nets,
        max_speed_type=input_id["type"],
    )
    return fig


@callback(
    Output({"out": "graph", "filter": MATCH, "type": MATCH, "is_sort_by_dist": True}, "figure"),
    Input(MD_FILTERS, "data"),
    Input({"out": "success_rate", "filter": MATCH, "type": MATCH, "is_sort_by_dist": True}, "on"),
    Input({"out": "sort_by_dist", "filter": MATCH, "type": MATCH, "is_sort_by_dist": True}, "on"),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    State({"out": "graph", "filter": MATCH, "type": MATCH, "is_sort_by_dist": True}, "id"),
)
def get_dist_graph(meta_data_filters, is_success_rate, filter_by_dist, nets, effective_samples, input_id):
    if not nets:
        return no_update
    filter_name = input_id["filter"]
    filters = MAX_SPEED_DIST_FILTERS[filter_name]
    interesting_filters = filters[1] if filter_by_dist else filters[0]
    fig = get_fig_by_filter(
        effective_samples=effective_samples,
        filter_name=filter_name,
        interesting_filters=interesting_filters,
        is_success_rate=is_success_rate,
        meta_data_filters=meta_data_filters,
        nets=nets,
        max_speed_type=input_id["type"],
    )
    return fig


def get_fig_by_filter(
    effective_samples, filter_name, max_speed_type, interesting_filters, is_success_rate, meta_data_filters, nets
):
    filter_name_to_display = " ".join(filter_name.split("_")).capitalize()
    pred_key = "vmax_binary_pred" if max_speed_type == VMAX_TYPE_KEY else "vlimit_pred"
    title = f"{max_speed_type.capitalize()} {'Success Rate' if is_success_rate else 'Fb Score'} per {filter_name_to_display}"
    fig = get_max_speed_fig(
        meta_data_filters=meta_data_filters,
        is_success_rate=is_success_rate,
        nets=nets,
        label="vlimit_label",
        pred=pred_key,
        interesting_filters=interesting_filters,
        effective_samples=effective_samples,
        title=title,
    )
    return fig


def get_max_speed_fig(
    meta_data_filters, is_success_rate, nets, label, pred, interesting_filters, effective_samples, title=""
):
    if is_success_rate:
        fig = get_max_speed_success_rate_fig(
            meta_data_filters, nets, label, pred, interesting_filters, effective_samples, title
        )
    else:
        fig = get_max_speed_fb_fig(meta_data_filters, nets, label, pred, interesting_filters, effective_samples, title)

    return fig


def get_max_speed_success_rate_fig(
    meta_data_filters, nets, label, pred, interesting_filters, effective_samples, title=""
):
    query = generate_vmax_success_rate_query(
        nets["frame_tables"],
        nets["meta_data"],
        label,
        pred,
        interesting_filters,
        meta_data_filters=meta_data_filters,
        extra_filters=f"{label} != 0",
    )
    data, _ = run_query_with_nets_names_processing(query)
    fig = draw_meta_data_filters(
        data, list(interesting_filters.keys()), calc_success_rate, effective_samples=effective_samples, title=title
    )
    return fig


def get_max_speed_fb_fig(meta_data_filters, nets, label, pred, interesting_filters, effective_samples, title=""):
    query = generate_vmax_fb_query(
        nets["frame_tables"],
        nets["meta_data"],
        label,
        pred,
        interesting_filters,
        meta_data_filters=meta_data_filters,
        extra_filters=f"{label} != 0",
    )
    data, _ = run_query_with_nets_names_processing(query)
    fig = draw_meta_data_filters(
        data, list(interesting_filters.keys()), calc_fb_per_row, effective_samples=effective_samples, title=title
    )
    return fig


def calc_success_rate(row, filter):
    tp = row[f"tp_{filter}"]
    tn = row[f"tn_{filter}"]
    overall = row[f"overall_{filter}"]
    if not overall:
        return
    success_rate = (tp + tn) / overall
    return success_rate
