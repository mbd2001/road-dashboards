import dash_daq as daq
import dash_bootstrap_components as dbc
from dash import html, dcc, register_page, Input, Output, callback, State, no_update

from road_eval_dashboard.components.common_filters import (
    ROAD_TYPE_FILTERS,
    LANE_MARK_TYPE_FILTERS,
    CURVE_BY_DIST_FILTERS,
    EVENT_FILTERS,
    WEATHER_FILTERS,
    CURVE_BY_RAD_FILTERS,
)
from road_eval_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper

from road_eval_dashboard.components import (
    meta_data_filter,
    base_dataset_statistics,
)
from road_eval_dashboard.components.components_ids import (
    MD_FILTERS,
    EMDP_ROAD_TYPE,
    EMDP_ROAD_TYPE_WORLD,
    EMDP_ROAD_TYPE_PRECISION,
    EMDP_LANE_MARK_TYPE,
    EMDP_LANE_MARK_TYPE_WORLD,
    EMDP_LANE_MARK_TYPE_PRECISION,
    EMDP_CURVE,
    EMDP_CURVE_WORLD,
    EMDP_CURVE_PRECISION,
    EMDP_EVENT,
    EMDP_EVENT_WORLD,
    EMDP_EVENT_PRECISION,
    EMDP_WEATHER_WORLD,
    EMDP_WEATHER,
    EMDP_WEATHER_PRECISION,
    EMDP_CURVE_BY_DIST,
    EFFECTIVE_SAMPLES_PER_BATCH,
    NETS,
)
from road_eval_dashboard.components.queries_manager import (
    run_query_with_nets_names_processing,
    generate_emdp_query,
)
from road_eval_dashboard.components.page_properties import PageProperties
from road_eval_dashboard.graphs.meta_data_filters_graph import draw_meta_data_filters

extra_properties = PageProperties("line-chart")
register_page(__name__, path="/emdp", name="Emdp", order=6, **extra_properties.__dict__)


def get_base_graph_layout(graph_id, image_to_world_id, avail_to_precision_id, sort_by_dist_id=None):
    layout = card_wrapper(
        [
            dbc.Row(loading_wrapper([dcc.Graph(id=graph_id, config={"displayModeBar": False})])),
            dbc.Stack(
                [
                    daq.BooleanSwitch(
                        id=image_to_world_id,
                        on=False,
                        label="Image <-> World",
                        labelPosition="top",
                    ),
                    daq.BooleanSwitch(
                        id=avail_to_precision_id,
                        on=False,
                        label="Avail <-> Precision",
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
                        )
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
        html.H1("Emdp Metrics", className="mb-5"),
        meta_data_filter.layout,
        base_dataset_statistics.frame_layout,
        get_base_graph_layout(EMDP_ROAD_TYPE, EMDP_ROAD_TYPE_WORLD, EMDP_ROAD_TYPE_PRECISION),
        get_base_graph_layout(EMDP_LANE_MARK_TYPE, EMDP_LANE_MARK_TYPE_WORLD, EMDP_LANE_MARK_TYPE_PRECISION),
        get_base_graph_layout(EMDP_CURVE, EMDP_CURVE_WORLD, EMDP_CURVE_PRECISION, EMDP_CURVE_BY_DIST),
        get_base_graph_layout(EMDP_EVENT, EMDP_EVENT_WORLD, EMDP_EVENT_PRECISION),
        get_base_graph_layout(EMDP_WEATHER, EMDP_WEATHER_WORLD, EMDP_WEATHER_PRECISION),
    ]
)


@callback(
    Output(EMDP_ROAD_TYPE, "figure"),
    Input(MD_FILTERS, "data"),
    Input(EMDP_ROAD_TYPE_WORLD, "on"),
    Input(EMDP_ROAD_TYPE_PRECISION, "on"),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    background=True,
)
def get_emdp_road_type(meta_data_filters, is_world, is_precision, nets, effective_samples):
    if not nets:
        return no_update

    fig = get_emdp_fig(
        meta_data_filters=meta_data_filters,
        nets=nets,
        interesting_filters=ROAD_TYPE_FILTERS,
        effective_samples=effective_samples,
        is_world=is_world,
        is_precision=is_precision,
        filter_name="Road Type",
    )
    return fig


@callback(
    Output(EMDP_LANE_MARK_TYPE, "figure"),
    Input(MD_FILTERS, "data"),
    Input(EMDP_LANE_MARK_TYPE_WORLD, "on"),
    Input(EMDP_LANE_MARK_TYPE_PRECISION, "on"),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    background=True,
)
def get_emdp_lane_mark_type(meta_data_filters, is_world, is_precision, nets, effective_samples):
    if not nets:
        return no_update

    fig = get_emdp_fig(
        meta_data_filters=meta_data_filters,
        nets=nets,
        interesting_filters=LANE_MARK_TYPE_FILTERS,
        effective_samples=effective_samples,
        is_world=is_world,
        is_precision=is_precision,
        filter_name="Lane Mark Type",
    )
    return fig


@callback(
    Output(EMDP_CURVE, "figure"),
    Input(MD_FILTERS, "data"),
    Input(EMDP_CURVE_WORLD, "on"),
    Input(EMDP_CURVE_BY_DIST, "on"),
    Input(EMDP_CURVE_PRECISION, "on"),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    background=True,
)
def get_emdp_curve(meta_data_filters, is_world, by_dist, is_precision, nets, effective_samples):
    if not nets:
        return no_update

    interesting_filters = CURVE_BY_DIST_FILTERS if by_dist else CURVE_BY_RAD_FILTERS
    fig = get_emdp_fig(
        meta_data_filters=meta_data_filters,
        nets=nets,
        interesting_filters=interesting_filters,
        effective_samples=effective_samples,
        is_world=is_world,
        is_precision=is_precision,
        filter_name="Curve",
    )
    return fig


@callback(
    Output(EMDP_EVENT, "figure"),
    Input(MD_FILTERS, "data"),
    Input(EMDP_EVENT_WORLD, "on"),
    Input(EMDP_EVENT_PRECISION, "on"),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    background=True,
)
def get_emdp_event(meta_data_filters, is_world, is_precision, nets, effective_samples):
    if not nets:
        return no_update

    fig = get_emdp_fig(
        meta_data_filters=meta_data_filters,
        nets=nets,
        interesting_filters=EVENT_FILTERS,
        effective_samples=effective_samples,
        is_world=is_world,
        is_precision=is_precision,
        filter_name="Event",
    )
    return fig


@callback(
    Output(EMDP_WEATHER, "figure"),
    Input(MD_FILTERS, "data"),
    Input(EMDP_WEATHER_WORLD, "on"),
    Input(EMDP_WEATHER_PRECISION, "on"),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    background=True,
)
def get_emdp_weather(meta_data_filters, is_world, is_precision, nets, effective_samples):
    if not nets:
        return no_update

    fig = get_emdp_fig(
        meta_data_filters=meta_data_filters,
        nets=nets,
        interesting_filters=WEATHER_FILTERS,
        effective_samples=effective_samples,
        is_world=is_world,
        is_precision=is_precision,
        filter_name="Weather Type",
    )
    return fig


def get_emdp_fig(meta_data_filters, nets, interesting_filters, effective_samples, is_world, is_precision, filter_name):
    label = (
        ("is_matched_world" if is_world else "is_matched")
        if is_precision
        else ("is_avail_world" if is_world else "is_avail")
    )
    query = generate_emdp_query(
        nets["frame_tables"],
        nets["meta_data"],
        label,
        1,
        interesting_filters,
        meta_data_filters=meta_data_filters,
        extra_filters=f"{label} != -1",
    )
    data, _ = run_query_with_nets_names_processing(query)
    world_str = "World" if is_world else "Image"
    precision_str = "Precision" if is_precision else "Availability"
    fig = draw_meta_data_filters(
        data,
        list(interesting_filters.keys()),
        get_emdp_score,
        effective_samples=effective_samples,
        title=f"Emdp {precision_str} in {world_str} per {filter_name}",
        yaxis="Score",
    )
    return fig


def get_emdp_score(row, filter):
    score = row[f"score_{filter}"]
    return score
