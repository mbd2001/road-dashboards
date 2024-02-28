import dash_daq as daq
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
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
    NETS, EMDP_VIEW_RANGE_HISTOGRAM, EMDP_VIEW_RANGE_HISTOGRAM_NAIVE_Z, EMDP_VIEW_RANGE_HISTOGRAM_CUMULATIVE,
    EMDP_VIEW_RANGE_HISTOGRAM_MONOTONIC, EMDP_VIEW_RANGE_HISTOGRAM_NORM, EMDP_VIEW_RANGE_HISTOGRAM_BY_SEC,
)
from road_eval_dashboard.components.queries_manager import (
    run_query_with_nets_names_processing,
    generate_emdp_query, generate_emdp_view_range_Z_histogram_query, generate_emdp_view_range_sec_histogram_query,
    _get_emdp_view_range_col,
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
                    )
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

def get_view_range_histogram_layout():
    return card_wrapper(
        [
            dbc.Row(
                [
                    dbc.Col(
                        loading_wrapper([dcc.Graph(id=EMDP_VIEW_RANGE_HISTOGRAM, config={"displayModeBar": False})]),
                        width=11,
                    )
                ]
            ),
            dbc.Stack([
            daq.BooleanSwitch(
                id=EMDP_VIEW_RANGE_HISTOGRAM_NAIVE_Z,
                on=False,
                label="use naive Z",
                labelPosition="top",
            ),
            daq.BooleanSwitch(
                id=EMDP_VIEW_RANGE_HISTOGRAM_CUMULATIVE,
                on=True,
                label="cumulative graph",
                labelPosition="top",
            ),
                daq.BooleanSwitch(
                    id=EMDP_VIEW_RANGE_HISTOGRAM_MONOTONIC,
                    on=True,
                    label="filter none monotonic",
                    labelPosition="top",
                ),
                daq.BooleanSwitch(
                    id=EMDP_VIEW_RANGE_HISTOGRAM_NORM,
                    on=True,
                    label="norm",
                    labelPosition="top",
                ),
                daq.BooleanSwitch(
                    id=EMDP_VIEW_RANGE_HISTOGRAM_BY_SEC,
                    on=True,
                    label="by sec",
                    labelPosition="top",
                ),
                ], direction="horizontal",
                gap=3,)
        ]
    )


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
        get_view_range_histogram_layout()
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

@callback(
    Output(EMDP_VIEW_RANGE_HISTOGRAM, "figure"),
    Input(MD_FILTERS, "data"),
    Input(EMDP_VIEW_RANGE_HISTOGRAM_NAIVE_Z, "on"),
    Input(EMDP_VIEW_RANGE_HISTOGRAM_CUMULATIVE, "on"),
    Input(EMDP_VIEW_RANGE_HISTOGRAM_MONOTONIC, "on"),
    Input(EMDP_VIEW_RANGE_HISTOGRAM_NORM, "on"),
    Input(EMDP_VIEW_RANGE_HISTOGRAM_BY_SEC, "on"),
    Input(NETS, "data"),
    background=True
)
def get_view_range_histogram_plot(meta_data_filters, naive_Z, cumulative, monotonic, norm, by_sec, nets):
    if not nets:
        return no_update
    xaxis_direction=None
    BIN_SIZE = 10
    max_Z_col = "max_Z"
    max_Z_col = _get_emdp_view_range_col(max_Z_col, naive_Z, monotonic)
    df, _ = _get_histogram_df(BIN_SIZE, max_Z_col, by_sec, meta_data_filters, monotonic, naive_Z, nets)
    df.loc[pd.isna(df[max_Z_col]), 'overall'] = 0
    if cumulative:
        cumsum_df = df.copy().groupby(['net_id', max_Z_col]).sum()[::-1].groupby(level=0).cumsum().reset_index()
        cumsum_df['score'] = cumsum_df['overall']
        cumsum_df['overall'] = df['overall']
        df = cumsum_df
        xaxis_direction='reversed'
    else:
        df['score'] = df['overall']
    if norm:
        df['score'] = df['score'] / df.groupby(['net_id'])['overall'].transform('sum')
    df.sort_values(by=["net_id", max_Z_col], inplace=True)
    fig = px.line(
        df,
        x=max_Z_col,
        y="score",
        color="net_id",
        markers=True,
        hover_data={max_Z_col: True, "net_id": False, "overall": True},
        labels={max_Z_col: "Z", "overall": "Count", },
    )
    fig.update_layout(
        title=f"<b>View Range Histogram<b>",
        xaxis_title="Z(m)",
        yaxis_title="Count",
        font=dict(size=16),
        hoverlabel=dict(font_size=16),
        xaxis=dict(autorange=xaxis_direction)
    )
    return fig


def _get_histogram_df(BIN_SIZE, column_name, by_sec, meta_data_filters, monotonic, naive_Z, nets):
    if by_sec:
        query = generate_emdp_view_range_sec_histogram_query(nets["frame_tables"],
                                                             nets["meta_data"],
                                                             meta_data_filters=meta_data_filters,
                                                             naive_Z=naive_Z,
                                                             use_monotonic=monotonic)
        df, _ = run_query_with_nets_names_processing(query)
        melted_df = df.melt(id_vars=["net_id"], var_name="column", value_name="overall")
        melted_df[column_name] = melted_df["column"].str.removesuffix('_world').str.removesuffix('_monotonic').str.split("_").str[-1].astype(float)
        melted_df.drop(columns=["column"], inplace=True)
        return melted_df, _
    query = generate_emdp_view_range_Z_histogram_query(
        nets["frame_tables"],
        nets["meta_data"],
        bin_size=BIN_SIZE,
        meta_data_filters=meta_data_filters,
        naive_Z=naive_Z,
        use_monotonic=monotonic
    )
    return run_query_with_nets_names_processing(query)


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
