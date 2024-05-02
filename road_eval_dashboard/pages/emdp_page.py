import dash_bootstrap_components as dbc
import dash_daq as daq
import pandas as pd
import plotly.express as px
from dash import MATCH, Input, Output, State, callback, dcc, html, no_update, register_page

from road_eval_dashboard.components import base_dataset_statistics, meta_data_filter
from road_eval_dashboard.components.common_filters import (
    CURVE_BY_DIST_FILTERS,
    CURVE_BY_RAD_FILTERS,
    EVENT_FILTERS,
    LANE_MARK_TYPE_FILTERS,
    ROAD_TYPE_FILTERS,
    WEATHER_FILTERS,
)
from road_eval_dashboard.components.components_ids import (
    EFFECTIVE_SAMPLES_PER_BATCH,
    EMDP_VIEW_RANGE_HISTOGRAM,
    EMDP_VIEW_RANGE_HISTOGRAM_BY_SEC,
    EMDP_VIEW_RANGE_HISTOGRAM_CUMULATIVE,
    EMDP_VIEW_RANGE_HISTOGRAM_MONOTONIC,
    EMDP_VIEW_RANGE_HISTOGRAM_NAIVE_Z,
    EMDP_VIEW_RANGE_HISTOGRAM_NORM,
    MD_FILTERS,
    NETS,
)
from road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_eval_dashboard.components.layout_wrapper import card_wrapper
from road_eval_dashboard.components.page_properties import PageProperties
from road_eval_dashboard.components.queries_manager import (
    _get_emdp_col,
    generate_emdp_query,
    generate_emdp_view_range_sec_histogram_query,
    generate_emdp_view_range_Z_histogram_query,
    run_query_with_nets_names_processing,
)
from road_eval_dashboard.graphs.meta_data_filters_graph import draw_meta_data_filters

extra_properties = PageProperties("line-chart")
register_page(__name__, path="/emdp", name="Emdp", order=6, **extra_properties.__dict__)

EMDP_TYPE = "emdp"
EMDP_FILTERS = {
    "road_type": {"filters": ROAD_TYPE_FILTERS},
    "lane_mark_type": {"filters": LANE_MARK_TYPE_FILTERS},
    "event": {"filters": EVENT_FILTERS},
    "weather": {"filters": WEATHER_FILTERS},
    "curve": {"filters": CURVE_BY_RAD_FILTERS, "dist_filters": CURVE_BY_DIST_FILTERS, "sort_by_dist": True},
}
HISTOGRAM_BOOLEAN_SWITCHES = [
    {
        "id": EMDP_VIEW_RANGE_HISTOGRAM_NAIVE_Z,
        "on": False,
        "label": "use naive Z",
    },
    {
        "id": EMDP_VIEW_RANGE_HISTOGRAM_CUMULATIVE,
        "on": True,
        "label": "cumulative graph",
    },
    {
        "id": EMDP_VIEW_RANGE_HISTOGRAM_MONOTONIC,
        "on": True,
        "label": "filter none monotonic",
    },
    {
        "id": EMDP_VIEW_RANGE_HISTOGRAM_NORM,
        "on": True,
        "label": "norm",
    },
    {
        "id": EMDP_VIEW_RANGE_HISTOGRAM_BY_SEC,
        "on": True,
        "label": "by sec",
    },
]


def get_base_graph_layout(filter_name, sort_by_dist=False):
    layout = card_wrapper(
        [
            dbc.Row(
                graph_wrapper(
                    {"out": "graph", "filter": filter_name, "emdp_type": EMDP_TYPE, "sort_by_dist": sort_by_dist}
                )
            ),
            dbc.Stack(
                [
                    daq.BooleanSwitch(
                        id={
                            "out": "image_world",
                            "filter": filter_name,
                            "emdp_type": EMDP_TYPE,
                            "sort_by_dist": sort_by_dist,
                        },
                        on=False,
                        label="Image <-> World",
                        labelPosition="top",
                        persistence=True,
                        persistence_type="session",
                    ),
                    daq.BooleanSwitch(
                        id={
                            "out": "avail_precision",
                            "filter": filter_name,
                            "emdp_type": EMDP_TYPE,
                            "sort_by_dist": sort_by_dist,
                        },
                        on=False,
                        label="Avail <-> Precision",
                        labelPosition="top",
                        persistence=True,
                        persistence_type="session",
                    ),
                    daq.BooleanSwitch(
                        id={
                            "out": "monotonic",
                            "filter": filter_name,
                            "emdp_type": EMDP_TYPE,
                            "sort_by_dist": sort_by_dist,
                        },
                        on=True,
                        label="filter none monotonic",
                        labelPosition="top",
                        persistence=True,
                        persistence_type="session",
                    ),
                    dbc.Tooltip(
                        "only relevant to availability mode",
                        target={
                            "out": "monotonic",
                            "filter": filter_name,
                            "emdp_type": EMDP_TYPE,
                            "sort_by_dist": sort_by_dist,
                        },
                    ),
                ]
                + (
                    [
                        daq.BooleanSwitch(
                            id={
                                "out": "sort_by_dist",
                                "filter": filter_name,
                                "emdp_type": EMDP_TYPE,
                                "sort_by_dist": sort_by_dist,
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
                )
                + [
                    html.Div(
                        [
                            dcc.Slider(
                                id={
                                    "out": "sec_slider",
                                    "filter": filter_name,
                                    "emdp_type": EMDP_TYPE,
                                    "sort_by_dist": sort_by_dist,
                                },
                                min=0,
                                max=5,
                                step=0.5,
                                value=1.5,
                            ),
                            html.Label("Sec", style={"text-align": "center"}),
                            dbc.Tooltip(
                                "only relevant to availability mode",
                                target={
                                    "out": "sec_slider",
                                    "filter": filter_name,
                                    "emdp_type": EMDP_TYPE,
                                    "sort_by_dist": sort_by_dist,
                                },
                                placement="bottom",
                            ),
                        ],
                        style={"width": "80%", "text-align": "center"},
                    ),
                ],
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
                        graph_wrapper(EMDP_VIEW_RANGE_HISTOGRAM),
                        width=11,
                    )
                ]
            ),
            dbc.Stack(
                [
                    daq.BooleanSwitch(
                        id=boolean_switch_setting["id"],
                        on=boolean_switch_setting["on"],
                        label=boolean_switch_setting["label"],
                        labelPosition="top",
                        persistence=True,
                        persistence_type="session",
                    )
                    for boolean_switch_setting in HISTOGRAM_BOOLEAN_SWITCHES
                ],
                direction="horizontal",
                gap=3,
            ),
        ]
    )


layout = html.Div(
    [
        html.H1("Emdp Metrics", className="mb-5"),
        meta_data_filter.layout,
        base_dataset_statistics.frame_layout,
        get_view_range_histogram_layout(),
    ]
    + [
        get_base_graph_layout(filter_name, sort_by_dist=filter_props.get("sort_by_dist", False))
        for filter_name, filter_props in EMDP_FILTERS.items()
    ]
)


@callback(
    Output({"out": "graph", "filter": MATCH, "emdp_type": EMDP_TYPE, "sort_by_dist": False}, "figure"),
    Output({"out": "monotonic", "filter": MATCH, "emdp_type": EMDP_TYPE, "sort_by_dist": False}, "disabled"),
    Output({"out": "sec_slider", "filter": MATCH, "emdp_type": EMDP_TYPE, "sort_by_dist": False}, "disabled"),
    Input(MD_FILTERS, "data"),
    Input({"out": "image_world", "filter": MATCH, "emdp_type": EMDP_TYPE, "sort_by_dist": False}, "on"),
    Input({"out": "avail_precision", "filter": MATCH, "emdp_type": EMDP_TYPE, "sort_by_dist": False}, "on"),
    Input({"out": "monotonic", "filter": MATCH, "emdp_type": EMDP_TYPE, "sort_by_dist": False}, "on"),
    Input({"out": "sec_slider", "filter": MATCH, "emdp_type": EMDP_TYPE, "sort_by_dist": False}, "value"),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    State({"out": "graph", "filter": MATCH, "emdp_type": EMDP_TYPE, "sort_by_dist": False}, "id"),
    background=True,
)
def get_none_dist_graph(
    meta_data_filters, is_world, is_precision, filter_none_monotonic, sec_to_check, nets, effective_samples, graph_id
):
    if not nets:
        return no_update, no_update, no_update
    filter_name = graph_id["filter"]
    filters = EMDP_FILTERS[filter_name]
    interesting_filters = filters["filters"]
    fig = get_emdp_fig(
        meta_data_filters=meta_data_filters,
        nets=nets,
        interesting_filters=interesting_filters,
        effective_samples=effective_samples,
        is_world=is_world,
        is_precision=is_precision,
        filter_name=filter_name,
        filter_none_monotonic=filter_none_monotonic and not is_precision,
        sec_to_check=sec_to_check,
    )
    return fig, is_precision, is_precision


@callback(
    Output({"out": "graph", "filter": MATCH, "emdp_type": EMDP_TYPE, "sort_by_dist": True}, "figure"),
    Output({"out": "monotonic", "filter": MATCH, "emdp_type": EMDP_TYPE, "sort_by_dist": True}, "disabled"),
    Output({"out": "sec_slider", "filter": MATCH, "emdp_type": EMDP_TYPE, "sort_by_dist": True}, "disabled"),
    Input(MD_FILTERS, "data"),
    Input({"out": "image_world", "filter": MATCH, "emdp_type": EMDP_TYPE, "sort_by_dist": True}, "on"),
    Input({"out": "avail_precision", "filter": MATCH, "emdp_type": EMDP_TYPE, "sort_by_dist": True}, "on"),
    Input({"out": "monotonic", "filter": MATCH, "emdp_type": EMDP_TYPE, "sort_by_dist": True}, "on"),
    Input({"out": "sec_slider", "filter": MATCH, "emdp_type": EMDP_TYPE, "sort_by_dist": True}, "value"),
    Input({"out": "sort_by_dist", "filter": MATCH, "emdp_type": EMDP_TYPE, "sort_by_dist": True}, "on"),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    State({"out": "graph", "filter": MATCH, "emdp_type": EMDP_TYPE, "sort_by_dist": True}, "id"),
    background=True,
)
def get_dist_graph(
    meta_data_filters,
    is_world,
    is_precision,
    filter_none_monotonic,
    sec_to_check,
    by_dist,
    nets,
    effective_samples,
    graph_id,
):
    if not nets:
        return no_update, no_update, no_update
    filter_name = graph_id["filter"]
    filters = EMDP_FILTERS[filter_name]
    interesting_filters = filters["dist_filters"] if by_dist else filters["filters"]
    fig = get_emdp_fig(
        meta_data_filters=meta_data_filters,
        nets=nets,
        interesting_filters=interesting_filters,
        effective_samples=effective_samples,
        is_world=is_world,
        is_precision=is_precision,
        filter_name=filter_name,
        filter_none_monotonic=filter_none_monotonic and not is_precision,
        sec_to_check=sec_to_check,
    )
    return fig, is_precision, is_precision


@callback(
    Output(EMDP_VIEW_RANGE_HISTOGRAM, "figure"),
    Input(MD_FILTERS, "data"),
    Input(EMDP_VIEW_RANGE_HISTOGRAM_NAIVE_Z, "on"),
    Input(EMDP_VIEW_RANGE_HISTOGRAM_CUMULATIVE, "on"),
    Input(EMDP_VIEW_RANGE_HISTOGRAM_MONOTONIC, "on"),
    Input(EMDP_VIEW_RANGE_HISTOGRAM_NORM, "on"),
    Input(EMDP_VIEW_RANGE_HISTOGRAM_BY_SEC, "on"),
    Input(NETS, "data"),
    background=True,
)
def get_view_range_histogram_plot(meta_data_filters, naive_Z, cumulative, monotonic, norm, by_sec, nets):
    if not nets:
        return no_update
    xaxis_direction = None
    BIN_SIZE = 10
    max_Z_col = "max_Z"
    max_Z_col = _get_emdp_col(max_Z_col, naive_Z, monotonic)
    df, _ = _get_histogram_df(BIN_SIZE, max_Z_col, by_sec, meta_data_filters, monotonic, naive_Z, nets)
    df.loc[pd.isna(df[max_Z_col]), "overall"] = 0
    if cumulative:
        cumsum_df = df.copy().groupby(["net_id", max_Z_col]).sum()[::-1].groupby(level=0).cumsum().reset_index()
        cumsum_df["score"] = cumsum_df["overall"]
        df = df.sort_values(by=["net_id", max_Z_col]).reset_index()
        cumsum_df = cumsum_df.sort_values(by=["net_id", max_Z_col]).reset_index()
        cumsum_df["overall"] = df["overall"]
        df = cumsum_df
        xaxis_direction = "reversed"
    else:
        df["score"] = df["overall"]
    if norm:
        df["score"] = df["score"] / df.groupby(["net_id"])["overall"].transform("sum")
    df.sort_values(by=["net_id", max_Z_col], inplace=True)
    fig = px.line(
        df,
        x=max_Z_col,
        y="score",
        color="net_id",
        markers=True,
        hover_data={max_Z_col: True, "net_id": False, "overall": True},
        labels={
            max_Z_col: "Z",
            "overall": "Count",
        },
    )
    fig.update_layout(
        title=f"<b>View Range Histogram<b>",
        xaxis_title="Z (sec)" if by_sec else "Z(m)",
        yaxis_title="Count",
        font=dict(size=16),
        hoverlabel=dict(font_size=16),
        xaxis=dict(autorange=xaxis_direction),
    )
    return fig


def _get_histogram_df(BIN_SIZE, column_name, by_sec, meta_data_filters, monotonic, naive_Z, nets):
    if by_sec:
        query = generate_emdp_view_range_sec_histogram_query(
            nets["frame_tables"],
            nets["meta_data"],
            meta_data_filters=meta_data_filters,
            naive_Z=naive_Z,
            use_monotonic=monotonic,
        )
        df, _ = run_query_with_nets_names_processing(query)
        melted_df = df.melt(id_vars=["net_id"], var_name="column", value_name="overall")
        melted_df[column_name] = (
            melted_df["column"]
            .str.removesuffix("_world")
            .str.removesuffix("_monotonic")
            .str.split("_")
            .str[-1]
            .astype(float)
        )
        melted_df.drop(columns=["column"], inplace=True)
        return melted_df, _
    query = generate_emdp_view_range_Z_histogram_query(
        nets["frame_tables"],
        nets["meta_data"],
        bin_size=BIN_SIZE,
        meta_data_filters=meta_data_filters,
        naive_Z=naive_Z,
        use_monotonic=monotonic,
    )
    return run_query_with_nets_names_processing(query)


def get_emdp_fig(
    meta_data_filters,
    nets,
    interesting_filters,
    effective_samples,
    is_world,
    is_precision,
    filter_none_monotonic,
    sec_to_check,
    filter_name,
):
    PRECISION_MATCHED = 1
    label = "is_matched" if is_precision else "Z_max_sec"
    label = _get_emdp_col(label, not is_world, filter_none_monotonic)
    pred = PRECISION_MATCHED if is_precision else sec_to_check
    query = generate_emdp_query(
        nets["frame_tables"],
        nets["meta_data"],
        label,
        pred,
        interesting_filters,
        meta_data_filters=meta_data_filters,
        extra_filters=f"{label} != -1",
    )
    data, _ = run_query_with_nets_names_processing(query)
    world_str = "World" if is_world else "Image"
    precision_str = "Precision" if is_precision else "Availability"
    filter_name_to_display = filter_name.replace("_", " ").capitalize()
    data = data.sort_values(by="net_id")
    fig = draw_meta_data_filters(
        data,
        list(interesting_filters.keys()),
        get_emdp_score,
        effective_samples=effective_samples,
        title=f"Emdp {precision_str} in {world_str} per {filter_name_to_display}",
        yaxis="Score",
    )
    return fig


def get_emdp_score(row, filter):
    score = row[f"score_{filter}"]
    return score
