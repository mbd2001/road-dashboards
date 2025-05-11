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
from road_dashboards.road_eval_dashboard.graphs.path_net_line_graph import draw_path_net_graph
from road_dashboards.road_eval_dashboard.utils.distances import SECONDS
from road_dashboards.road_eval_dashboard.utils.quality import quality_functions
from road_dashboards.road_eval_dashboard.utils.quality.quality_config import (
    METRIC_GRAPHS_SETTINGS,
    DPQualityQueryConfig,
    MetricType,
    get_hover_text_parts,
)


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
    """
    Update all quality graphs for the given role.
    """
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
    raw_counts_master_df, _ = run_query_with_nets_names_processing(query)

    if raw_counts_master_df.empty:
        return (no_update, no_update, no_update, no_update, no_update, no_update)

    metric_dfs = quality_functions.compute_metrics_from_count_df(raw_counts_master_df.copy())

    raw_counts_master_df_indexed = raw_counts_master_df.set_index("net_id")

    figs = {}
    for metric_type_enum_val, settings in METRIC_GRAPHS_SETTINGS.items():
        metric_df = metric_dfs[metric_type_enum_val]

        def generate_hover_text_for_metric(metric_series_row, sec_value, current_metric_type=metric_type_enum_val):
            net_id = metric_series_row.net_id
            rate_value = metric_series_row[sec_value]
            hover_parts = [f"Rate: {rate_value:.2%}"]

            raw_counts_for_net = raw_counts_master_df_indexed.loc[net_id]

            tp_col_name = f"tp_{sec_value}"
            fn_col_name = f"fn_{sec_value}"
            fp_col_name = f"fp_{sec_value}"
            tn_col_name = f"tn_{sec_value}"

            tp = raw_counts_for_net[tp_col_name]
            fn = raw_counts_for_net[fn_col_name]
            fp = raw_counts_for_net[fp_col_name]
            tn = raw_counts_for_net[tn_col_name]

            hover_parts.extend(get_hover_text_parts(current_metric_type, tp, fn, fp, tn))

            return "<br>".join(hover_parts)

        fig = draw_path_net_graph(
            data=metric_df,
            cols=SECONDS,
            title=settings["title"],
            role=role,
            yaxis=settings["yaxis"],
            plot_bgcolor=settings["bg"],
            score_func=lambda row, sec: row[sec],
            hover=True,
            hover_func=generate_hover_text_for_metric,
        )
        figs[metric_type_enum_val] = fig

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
    """
    Update the quality view range histogram for the given role.
    """
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

    return quality_functions.create_quality_view_range_histogram(df, role)
