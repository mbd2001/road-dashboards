import dash_bootstrap_components as dbc
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
    PATHNET_PRED,
)
from road_dashboards.road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_dashboards.road_eval_dashboard.components.layout_wrapper import card_wrapper
from road_dashboards.road_eval_dashboard.components.queries_manager import (
    DISTANCES,
    MetricType,
    QualityQueryConfig,
    build_metric_query,
    run_query_with_nets_names_processing,
)
from road_dashboards.road_eval_dashboard.graphs.path_net_line_graph import draw_path_net_graph
from road_dashboards.road_eval_dashboard.utils.colors import GREEN, RED, YELLOW


def get_graph_row(graph_type: str) -> dbc.Row:
    """Helper to create a row with two graph columns (host and non-host)."""
    return dbc.Row(
        [
            dbc.Col(graph_wrapper({"type": graph_type, "role": "host"}), width=6),
            dbc.Col(graph_wrapper({"type": graph_type, "role": "non-host"}), width=6),
        ]
    )


quality_layout = html.Div(
    [
        card_wrapper(
            [
                # Quality graphs
                get_graph_row(PATH_NET_QUALITY_ACCURACY),
                get_graph_row(PATH_NET_QUALITY_PRECISION),
                get_graph_row(PATH_NET_QUALITY_TP),
                get_graph_row(PATH_NET_QUALITY_TN),
                get_graph_row(PATH_NET_QUALITY_FP),
                get_graph_row(PATH_NET_QUALITY_FN),
                # Slider row
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
    """Updates all quality graphs at once for a given role."""
    if not nets:
        return (no_update, no_update, no_update, no_update, no_update, no_update)

    role = idx["role"]
    config = QualityQueryConfig(
        data_tables=nets[PATHNET_PRED],
        meta_data=nets["meta_data"],
        meta_data_filters=meta_data_filters,
        role=role,
        quality_thresh_filter=slider_values[0],
    )

    fig_tp = update_quality_graph(
        config,
        metric=MetricType.TPR,
        title="DPs Quality Score - True Positive Rate",
    )
    fig_fn = update_quality_graph(
        config,
        metric=MetricType.FNR,
        title="DPs Quality Score - False Negative Rate",
    )
    fig_tn = update_quality_graph(
        config,
        metric=MetricType.TNR,
        title="DPs Quality Score - True Negative Rate",
    )
    fig_fp = update_quality_graph(
        config,
        metric=MetricType.FPR,
        title="DPs Quality Score - False Positive Rate",
    )
    fig_acc = update_quality_graph(
        config,
        metric=MetricType.ACCURACY,
        title="DPs Quality Score - Accuracy",
    )
    fig_prec = update_quality_graph(
        config,
        metric=MetricType.PRECISION,
        title="DPs Quality Score - Precision",
    )

    return fig_tp, fig_fn, fig_tn, fig_fp, fig_acc, fig_prec


def update_quality_graph(config: QualityQueryConfig, metric: MetricType, title: str):
    """Helper to update a graph based on QualityQueryConfig and MetricType."""
    query = build_metric_query(config, metric)
    df, _ = run_query_with_nets_names_processing(query)
    match metric:
        case MetricType.TPR | MetricType.TNR:
            bg_color = GREEN
        case MetricType.FNR | MetricType.FPR:
            bg_color = RED
        case _:
            bg_color = YELLOW
    return draw_path_net_graph(
        data=df,
        cols=DISTANCES,
        title=title,
        role=config.role,
        yaxis=f"{metric.value} (%)",
        plot_bgcolor=bg_color,
    )
