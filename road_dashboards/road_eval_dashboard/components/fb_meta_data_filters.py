import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import Input, Output, State, callback, html, no_update
from road_database_toolkit.athena.athena_utils import query_athena

from road_dashboards.road_eval_dashboard.components.common_filters import (
    CURVE_BY_DIST_FILTERS,
    CURVE_BY_RAD_FILTERS,
    EVENT_FILTERS,
    LANE_MARK_COLOR_FILTERS,
    LANE_MARK_TYPE_FILTERS,
    ROAD_TYPE_FILTERS,
    WEATHER_FILTERS,
)
from road_dashboards.road_eval_dashboard.components.components_ids import (
    EFFECTIVE_SAMPLES_PER_BATCH,
    FB_PER_CURVE_BY_DIST,
    FB_PER_CURVE_GRAPH,
    FB_PER_CURVE_HOST,
    FB_PER_EVENT_GRAPH,
    FB_PER_EVENT_HOST,
    FB_PER_LANE_MARK_COLOR_GRAPH,
    FB_PER_LANE_MARK_COLOR_HOST,
    FB_PER_LANE_MARK_TYPE_GRAPH,
    FB_PER_LANE_MARK_TYPE_HOST,
    FB_PER_ROAD_TYPE_GRAPH,
    FB_PER_ROAD_TYPE_HOST,
    FB_PER_WEATHER_GRAPH,
    FB_PER_WEATHER_HOST,
    MD_FILTERS,
    NET_ID_TO_FB_BEST_THRESH,
    NETS,
)
from road_dashboards.road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_dashboards.road_eval_dashboard.components.layout_wrapper import card_wrapper
from road_dashboards.road_eval_dashboard.components.queries_manager import (
    generate_fb_query,
    run_query_with_nets_names_processing,
)
from road_dashboards.road_eval_dashboard.graphs.meta_data_filters_graph import calc_fb_per_row, draw_meta_data_filters
from road_dashboards.road_eval_dashboard.graphs.precision_recall_curve import calc_best_thresh


def get_base_graph_layout(graph_id, host_button_id, sort_by_dist_id=None):
    layout = card_wrapper(
        [
            dbc.Row(graph_wrapper(graph_id)),
            dbc.Stack(
                [
                    daq.BooleanSwitch(
                        id=host_button_id,
                        on=False,
                        label="Host Only",
                        labelPosition="top",
                    ),
                ]
                + (
                    [
                        daq.BooleanSwitch(
                            id=sort_by_dist_id,
                            on=False,
                            label="Sort By Dist",
                            labelPosition="top",
                        ),
                    ]
                    if sort_by_dist_id
                    else []
                ),
                direction="horizontal",
                gap=3,
            ),
        ]
    )
    return layout


layout = html.Div(
    [
        get_base_graph_layout(FB_PER_ROAD_TYPE_GRAPH, FB_PER_ROAD_TYPE_HOST),
        get_base_graph_layout(FB_PER_LANE_MARK_TYPE_GRAPH, FB_PER_LANE_MARK_TYPE_HOST),
        get_base_graph_layout(FB_PER_LANE_MARK_COLOR_GRAPH, FB_PER_LANE_MARK_COLOR_HOST),
        get_base_graph_layout(FB_PER_CURVE_GRAPH, FB_PER_CURVE_HOST, FB_PER_CURVE_BY_DIST),
        get_base_graph_layout(FB_PER_EVENT_GRAPH, FB_PER_EVENT_HOST),
        get_base_graph_layout(FB_PER_WEATHER_GRAPH, FB_PER_WEATHER_HOST),
    ]
)


@callback(
    Output(NET_ID_TO_FB_BEST_THRESH, "data"),
    Input(NETS, "data"),
)
def get_best_fb_per_net(nets):
    if not nets or not nets["gt_tables"] or not nets["pred_tables"]:
        return no_update

    query = generate_fb_query(
        nets["gt_tables"],
        nets["pred_tables"],
        nets["meta_data"],
    )
    data, _ = query_athena(database="run_eval_db", query=query, cache_duration_minutes=60 * 24 * 3)
    data = data.fillna(1)
    net_id_to_best_thresh = calc_best_thresh(data)
    return net_id_to_best_thresh


@callback(
    Output(FB_PER_ROAD_TYPE_GRAPH, "figure"),
    Input(MD_FILTERS, "data"),
    Input(FB_PER_ROAD_TYPE_HOST, "on"),
    State(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    Input(NET_ID_TO_FB_BEST_THRESH, "data"),
)
def fb_per_road_type(meta_data_filters, is_host, nets, effective_samples, thresh):
    if not nets or thresh is None:
        return no_update

    fig = get_fb_fig(
        meta_data_filters=meta_data_filters,
        nets=nets,
        interesting_filters=ROAD_TYPE_FILTERS,
        effective_samples=effective_samples,
        thresh=thresh if thresh else {net: 0 for net in nets["names"]},
        is_host=is_host,
        filter_name="Road Type",
    )
    return fig


@callback(
    Output(FB_PER_LANE_MARK_TYPE_GRAPH, "figure"),
    Input(MD_FILTERS, "data"),
    Input(FB_PER_LANE_MARK_TYPE_HOST, "on"),
    State(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    Input(NET_ID_TO_FB_BEST_THRESH, "data"),
)
def fb_per_lane_mark_type(meta_data_filters, is_host, nets, effective_samples, thresh):
    if not nets or thresh is None:
        return no_update

    fig = get_fb_fig(
        meta_data_filters=meta_data_filters,
        nets=nets,
        interesting_filters=LANE_MARK_TYPE_FILTERS,
        effective_samples=effective_samples,
        thresh=thresh if thresh else {net: 0 for net in nets["names"]},
        is_host=is_host,
        filter_name="Lane Mark Type",
    )
    return fig


@callback(
    Output(FB_PER_LANE_MARK_COLOR_GRAPH, "figure"),
    Input(MD_FILTERS, "data"),
    Input(FB_PER_LANE_MARK_COLOR_HOST, "on"),
    State(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    Input(NET_ID_TO_FB_BEST_THRESH, "data"),
)
def fb_per_lane_mark_color(meta_data_filters, is_host, nets, effective_samples, thresh):
    if not nets or thresh is None:
        return no_update

    fig = get_fb_fig(
        meta_data_filters=meta_data_filters,
        nets=nets,
        interesting_filters=LANE_MARK_COLOR_FILTERS,
        effective_samples=effective_samples,
        thresh=thresh if thresh else {net: 0 for net in nets["names"]},
        is_host=is_host,
        filter_name="Lane Mark Color",
    )
    return fig


@callback(
    Output(FB_PER_CURVE_GRAPH, "figure"),
    Input(MD_FILTERS, "data"),
    Input(FB_PER_CURVE_HOST, "on"),
    Input(FB_PER_CURVE_BY_DIST, "on"),
    State(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    Input(NET_ID_TO_FB_BEST_THRESH, "data"),
)
def fb_per_curve(meta_data_filters, is_host, by_dist, nets, effective_samples, thresh):
    if not nets or thresh is None:
        return no_update

    interesting_filters = CURVE_BY_DIST_FILTERS if by_dist else CURVE_BY_RAD_FILTERS
    fig = get_fb_fig(
        meta_data_filters=meta_data_filters,
        nets=nets,
        interesting_filters=interesting_filters,
        effective_samples=effective_samples,
        thresh=thresh if thresh else {net: 0 for net in nets["names"]},
        is_host=is_host,
        filter_name="Curve",
    )
    return fig


@callback(
    Output(FB_PER_EVENT_GRAPH, "figure"),
    Input(MD_FILTERS, "data"),
    Input(FB_PER_EVENT_HOST, "on"),
    State(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    Input(NET_ID_TO_FB_BEST_THRESH, "data"),
)
def fb_per_event(meta_data_filters, is_host, nets, effective_samples, thresh):
    if not nets or thresh is None:
        return no_update

    fig = get_fb_fig(
        meta_data_filters=meta_data_filters,
        nets=nets,
        interesting_filters=EVENT_FILTERS,
        effective_samples=effective_samples,
        thresh=thresh if thresh else {net: 0 for net in nets["names"]},
        is_host=is_host,
        filter_name="Event",
    )
    return fig


@callback(
    Output(FB_PER_WEATHER_GRAPH, "figure"),
    Input(MD_FILTERS, "data"),
    Input(FB_PER_WEATHER_HOST, "on"),
    State(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    Input(NET_ID_TO_FB_BEST_THRESH, "data"),
)
def fb_per_weather_type(meta_data_filters, is_host, nets, effective_samples, thresh):
    if not nets or thresh is None:
        return no_update

    fig = get_fb_fig(
        meta_data_filters=meta_data_filters,
        nets=nets,
        interesting_filters=WEATHER_FILTERS,
        effective_samples=effective_samples,
        thresh=thresh if thresh else {net: 0 for net in nets["names"]},
        is_host=is_host,
        filter_name="Weather Type",
    )
    return fig


def get_fb_fig(meta_data_filters, nets, interesting_filters, effective_samples, thresh, is_host, filter_name):
    query = generate_fb_query(
        nets["gt_tables"],
        nets["pred_tables"],
        nets["meta_data"],
        meta_data_filters=meta_data_filters,
        interesting_filters=interesting_filters,
        input_thresh=thresh,
        role="host" if is_host else "",
    )
    data, _ = run_query_with_nets_names_processing(query)
    data = data_post_process(data, interesting_filters.keys())
    host_str = "Host" if is_host else "Overall"
    fig = draw_meta_data_filters(
        data,
        list(interesting_filters.keys()),
        calc_fb_per_row,
        hover=True,
        effective_samples=effective_samples,
        title=f"{host_str} Fb per {filter_name}",
    )
    return fig


def data_post_process(data, filters):
    for filter in filters:
        data[f"recall_{filter}"] = data[f"count_{filter}"] / data[f"overall_{filter}"]
    return data
