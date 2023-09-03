import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import html, dcc, register_page, Input, Output, callback, State, no_update

from road_eval_dashboard.components.common_filters import (
    MAX_SPEED_FILTERS,
    CURVE_BY_RAD_FILTERS,
    CURVE_BY_DIST_FILTERS,
)
from road_eval_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper

from road_eval_dashboard.components import (
    meta_data_filter,
    base_dataset_statistics,
)
from road_eval_dashboard.components.components_ids import (
    MD_FILTERS,
    NETS,
    VMAX_ROAD_TYPE_SUCCESS_RATE,
    VMAX_CURVE_SUCCESS_RATE,
    VMAX_CURVE,
    VLIMIT_ROAD_TYPE_SUCCESS_RATE,
    VLIMIT_ROAD_TYPE,
    VLIMIT_CURVE_SUCCESS_RATE,
    VLIMIT_CURVE,
    VMAX_ROAD_TYPE,
    VLIMIT_CURVE_BY_DIST,
    VMAX_CURVE_BY_DIST,
    EFFECTIVE_SAMPLES_PER_BATCH,
)
from road_eval_dashboard.components.queries_manager import (
    run_query_with_nets_names_processing,
    generate_vmax_fb_query,
    generate_vmax_success_rate_query,
)
from road_eval_dashboard.components.page_properties import PageProperties
from road_eval_dashboard.graphs.meta_data_filters_graph import (
    draw_meta_data_filters,
    calc_fb_per_row,
)

f_beta = 1
B2 = f_beta**2


extra_properties = PageProperties("line-chart")
register_page(__name__, path="/max_speed", name="Max Speed", order=7, **extra_properties.__dict__)


def get_base_graph_layout(graph_id, fb_to_success_rate_id, sort_by_dist_id=None):
    layout = card_wrapper(
        [
            dbc.Row(loading_wrapper([dcc.Graph(id=graph_id, config={"displayModeBar": False})])),
            dbc.Stack(
                [
                    daq.BooleanSwitch(
                        id=fb_to_success_rate_id,
                        on=False,
                        label="Fb <-> Success Rate",
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
        html.H1("Max Speed Metrics", className="mb-5"),
        meta_data_filter.layout,
        base_dataset_statistics.frame_layout,
        get_base_graph_layout(VMAX_ROAD_TYPE, VMAX_ROAD_TYPE_SUCCESS_RATE),
        get_base_graph_layout(VMAX_CURVE, VMAX_CURVE_SUCCESS_RATE, VMAX_CURVE_BY_DIST),
        get_base_graph_layout(VLIMIT_ROAD_TYPE, VLIMIT_ROAD_TYPE_SUCCESS_RATE),
        get_base_graph_layout(VLIMIT_CURVE, VLIMIT_CURVE_SUCCESS_RATE, VLIMIT_CURVE_BY_DIST),
    ]
)


@callback(
    Output(VMAX_ROAD_TYPE, "figure"),
    Input(MD_FILTERS, "data"),
    Input(VMAX_ROAD_TYPE_SUCCESS_RATE, "on"),
    State(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    background=True,
)
def get_vmax_road_type(meta_data_filters, is_success_rate, nets, effective_samples):
    if not nets:
        return no_update

    title = f"VMax {'Success Rate' if is_success_rate else 'Fb Score'} per Road Type"
    fig = get_max_speed_fig(
        meta_data_filters=meta_data_filters,
        is_success_rate=is_success_rate,
        nets=nets,
        label="vlimit_label",
        pred="vmax_binary_pred",
        interesting_filters=MAX_SPEED_FILTERS,
        effective_samples=effective_samples,
        title=title,
    )
    return fig


@callback(
    Output(VMAX_CURVE, "figure"),
    Input(MD_FILTERS, "data"),
    Input(VMAX_CURVE_SUCCESS_RATE, "on"),
    Input(VMAX_CURVE_BY_DIST, "on"),
    State(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    background=True,
)
def get_vmax_curve(meta_data_filters, is_success_rate, by_dist, nets, effective_samples):
    if not nets:
        return no_update

    title = f"VMax {'Success Rate' if is_success_rate else 'Fb Score'} per Curve"
    interesting_filters = CURVE_BY_DIST_FILTERS if by_dist else CURVE_BY_RAD_FILTERS
    fig = get_max_speed_fig(
        meta_data_filters=meta_data_filters,
        is_success_rate=is_success_rate,
        nets=nets,
        label="vlimit_label",
        pred="vmax_binary_pred",
        interesting_filters=interesting_filters,
        effective_samples=effective_samples,
        title=title,
    )
    return fig


@callback(
    Output(VLIMIT_ROAD_TYPE, "figure"),
    Input(MD_FILTERS, "data"),
    Input(VLIMIT_ROAD_TYPE_SUCCESS_RATE, "on"),
    State(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    background=True,
)
def get_vlimit_road_type(meta_data_filters, is_success_rate, nets, effective_samples):
    if not nets:
        return no_update

    title = f"VLimit {'Success Rate' if is_success_rate else 'Fb Score'} per Road Type"
    fig = get_max_speed_fig(
        meta_data_filters=meta_data_filters,
        is_success_rate=is_success_rate,
        nets=nets,
        label="vlimit_label",
        pred="vlimit_pred",
        interesting_filters=MAX_SPEED_FILTERS,
        effective_samples=effective_samples,
        title=title,
    )
    return fig


@callback(
    Output(VLIMIT_CURVE, "figure"),
    Input(MD_FILTERS, "data"),
    Input(VLIMIT_CURVE_SUCCESS_RATE, "on"),
    Input(VLIMIT_CURVE_BY_DIST, "on"),
    State(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    background=True,
)
def get_vlimit_curve(meta_data_filters, is_success_rate, by_dist, nets, effective_samples):
    if not nets:
        return no_update

    label = "vlimit_label"
    pred = "vlimit_pred"
    title = f"VLimit {'Success Rate' if is_success_rate else 'Fb Score'} per Curve"
    interesting_filters = CURVE_BY_DIST_FILTERS if by_dist else CURVE_BY_RAD_FILTERS
    fig = get_max_speed_fig(
        meta_data_filters=meta_data_filters,
        is_success_rate=is_success_rate,
        nets=nets,
        label=label,
        pred=pred,
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
    success_rate = (tp + tn) / overall
    return success_rate
