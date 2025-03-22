import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import MATCH, Input, Output, State, callback, dcc, html, no_update

from road_dashboards.road_eval_dashboard.components.components_ids import (
    MD_FILTERS,
    NETS,
    PATH_NET_QUALITY_ACCURACY,
    PATH_NET_QUALITY_FN,
    PATH_NET_QUALITY_FP,
    PATH_NET_QUALITY_PRECISION,
    PATH_NET_QUALITY_TN,
    PATH_NET_QUALITY_TP,
    PATH_NET_QUALITY_VIEW_RANGE,
    PATHNET_PRED,
)
from road_dashboards.road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_dashboards.road_eval_dashboard.components.layout_wrapper import card_wrapper
from road_dashboards.road_eval_dashboard.components.queries_manager import (
    build_dp_all_quality_metrics_query,
    build_dp_quality_view_range_histogram_query,
    run_query_with_nets_names_processing,
)
from road_dashboards.road_eval_dashboard.graphs.histogram_plot import basic_histogram_plot
from road_dashboards.road_eval_dashboard.graphs.path_net_line_graph import draw_path_net_graph
from road_dashboards.road_eval_dashboard.utils.colors import GREEN, RED
from road_dashboards.road_eval_dashboard.utils.distances import SECONDS
from road_dashboards.road_eval_dashboard.utils.quality import quality_functions
from road_dashboards.road_eval_dashboard.utils.quality.quality_config import DPQualityQueryConfig, MetricType


def get_graph_row(graph_type: str) -> dbc.Row:
    """Helper to create a row with two graph columns (host and non-host)."""
    return dbc.Row(
        [
            dbc.Col(graph_wrapper({"type": graph_type, "role": "host"}), width=6),
            dbc.Col(graph_wrapper({"type": graph_type, "role": "non-host"}), width=6),
        ]
    )


def get_view_range_row() -> dbc.Row:
    """Helper to create a row with two view range histogram columns (host and non-host)."""
    return dbc.Row(
        [
            dbc.Col(graph_wrapper({"type": PATH_NET_QUALITY_VIEW_RANGE, "role": "host"}), width=6),
            dbc.Col(graph_wrapper({"type": PATH_NET_QUALITY_VIEW_RANGE, "role": "non-host"}), width=6),
        ]
    )


quality_layout = html.Div(
    [
        card_wrapper(
            [
                get_graph_row(PATH_NET_QUALITY_ACCURACY),
                get_graph_row(PATH_NET_QUALITY_PRECISION),
                get_graph_row(PATH_NET_QUALITY_TP),
                get_graph_row(PATH_NET_QUALITY_TN),
                get_graph_row(PATH_NET_QUALITY_FP),
                get_graph_row(PATH_NET_QUALITY_FN),
                get_view_range_row(),
                dbc.Row(
                    [
                        html.Label(
                            "quality-threshold (score)",
                            style={"text-align": "center", "fontSize": "20px"},
                        ),
                        dcc.RangeSlider(
                            id="quality-threshold-slider",
                            min=0,
                            max=1,
                            step=0.1,
                            value=[0.5],
                            allowCross=False,
                        ),
                    ]
                ),
            ]
        )
    ]
)


@callback(
    Output({"type": PATH_NET_QUALITY_TP, "role": MATCH}, "figure"),
    Output({"type": PATH_NET_QUALITY_FN, "role": MATCH}, "figure"),
    Output({"type": PATH_NET_QUALITY_TN, "role": MATCH}, "figure"),
    Output({"type": PATH_NET_QUALITY_FP, "role": MATCH}, "figure"),
    Output({"type": PATH_NET_QUALITY_ACCURACY, "role": MATCH}, "figure"),
    Output({"type": PATH_NET_QUALITY_PRECISION, "role": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
    Input("quality-threshold-slider", "value"),
    State({"type": PATH_NET_QUALITY_TP, "role": MATCH}, "id"),
)
def update_all_quality_graphs(meta_data_filters, nets, slider_values, idx):
    if not nets:
        return (no_update, no_update, no_update, no_update, no_update, no_update)

    role = idx["role"]
    config = DPQualityQueryConfig(
        data_tables=nets[PATHNET_PRED],
        meta_data=nets["meta_data"],
        meta_data_filters=meta_data_filters,
        role=role,
        quality_prob_score_thresh=slider_values[0],
    )

    query = build_dp_all_quality_metrics_query(config)
    df, _ = run_query_with_nets_names_processing(query)

    metric_dfs = quality_functions.compute_metrics_from_count_df(df)

    metric_settings = {
        MetricType.CORRECT_ACCEPTANCE_RATE: {
            "title": "Correct Acceptance Rate",
            "yaxis": "Correct Acceptance Rate (%)",
            "bg": GREEN,
        },
        MetricType.INCORRECT_ACCEPTANCE_RATE: {
            "title": "Incorrect Acceptance Rate",
            "yaxis": "Incorrect Acceptance Rate (%)",
            "bg": RED,
        },
        MetricType.CORRECT_REJECTION_RATE: {
            "title": "Correct Rejection Rate",
            "yaxis": "Correct Rejection Rate (%)",
            "bg": GREEN,
        },
        MetricType.INCORRECT_REJECTION_RATE: {
            "title": "Incorrect Rejection Rate",
            "yaxis": "Incorrect Rejection Rate (%)",
            "bg": RED,
        },
        MetricType.ACCURACY: {"title": "Accuracy", "yaxis": "Accuracy (%)", "bg": GREEN},
        MetricType.PRECISION: {"title": "Precision", "yaxis": "Precision (%)", "bg": GREEN},
    }

    figs = {}
    for metric, settings in metric_settings.items():
        metric_df = metric_dfs[metric]
        fig = draw_path_net_graph(
            data=metric_df,
            cols=SECONDS,
            title=settings["title"],
            role=role,
            yaxis=settings["yaxis"],
            plot_bgcolor=settings["bg"],
            score_func=lambda row, sec: row[sec],
        )
        figs[metric] = fig

    return (
        figs[MetricType.CORRECT_ACCEPTANCE_RATE],
        figs[MetricType.INCORRECT_ACCEPTANCE_RATE],
        figs[MetricType.CORRECT_REJECTION_RATE],
        figs[MetricType.INCORRECT_REJECTION_RATE],
        figs[MetricType.ACCURACY],
        figs[MetricType.PRECISION],
    )


@callback(
    Output({"type": PATH_NET_QUALITY_VIEW_RANGE, "role": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
    Input("quality-threshold-slider", "value"),
    State({"type": PATH_NET_QUALITY_VIEW_RANGE, "role": MATCH}, "id"),
)
def update_quality_view_range_histogram(meta_data_filters, nets, slider_values, idx):
    if not nets:
        return no_update

    role = idx["role"]
    config = DPQualityQueryConfig(
        data_tables=nets[PATHNET_PRED],
        meta_data=nets["meta_data"],
        meta_data_filters=meta_data_filters,
        role=role,
        quality_prob_score_thresh=slider_values[0],
    )

    query = build_dp_quality_view_range_histogram_query(config, bin_size=5)
    df, _ = run_query_with_nets_names_processing(query)

    return create_quality_view_range_histogram(df, role)


def create_quality_view_range_histogram(df: pd.DataFrame, role: str, bin_size: int = 5) -> go.Figure:
    """
    Create a histogram showing distribution of quality view range values
    where each bin represents count of points with view_range >= bin value.
    NOTICE: The value of the view range is not configurable, it is a constant value that is
    set at pathnet Stats based on threshold of 0.5.

    Args:
        df: DataFrame with quality_view_range and overall (count) columns
        role: Role type (host or non-host)
        bin_size: Size of bins in meters

    Returns:
        A plotly histogram figure
    """
    column_name = DPQualityQueryConfig.quality_view_range_column_name

    if df.empty or column_name not in df.columns:
        return go.Figure()

    df = df[df[column_name].notna()]

    if df.empty:
        return go.Figure()

    result_data = []

    for net_id in df["net_id"].unique():
        net_df = df[df["net_id"] == net_id]

        if len(net_df) > 0:
            min_value = max(0, net_df[column_name].min())
            max_value = net_df[column_name].max()

            min_bin = (min_value // bin_size) * bin_size
            max_bin = ((max_value // bin_size) + 1) * bin_size

            all_bins = np.arange(min_bin, max_bin + bin_size, bin_size)

            for bin_value in all_bins:
                count = net_df[net_df[column_name] >= bin_value]["overall"].sum()
                result_data.append({"bin": bin_value, "count": count, "net_id": net_id})

    hist_df = pd.DataFrame(result_data)

    title = f"Quality View Range Distribution ({role})"
    subtitle = "Height represents count of paths with view range >= bin value"
    full_title = f"<b>{title}</b><br><sup>{subtitle}</sup>"

    return basic_histogram_plot(data=hist_df, x="bin", y="count", title=full_title, color="net_id")
