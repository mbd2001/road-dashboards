import dash_bootstrap_components as dbc
from dash import Input, Output, callback, html, no_update

from road_dashboards.road_eval_dashboard.components.components_ids import (
    MD_FILTERS,
    NETS,
    PATHNET_FILTERS,
    PATHNET_MID_MATCHED_INPUT_SOURCE_ALL,
    PATHNET_MID_MATCHED_INPUT_SOURCE_HOST,
    PATHNET_MID_MATCHED_INPUT_SOURCE_NON_HOST,
    PATHNET_MID_MATCHED_PRED_SOURCE_ALL,
    PATHNET_MID_MATCHED_PRED_SOURCE_HOST,
    PATHNET_MID_MATCHED_PRED_SOURCE_NON_HOST,
    PATHNET_MID_PRED_SOURCE,
)
from road_dashboards.road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_dashboards.road_eval_dashboard.components.layout_wrapper import card_wrapper
from road_dashboards.road_eval_dashboard.components.queries_manager import (
    generate_count_query,
    run_query_with_nets_names_processing,
)
from road_dashboards.road_eval_dashboard.graphs.bar_graph import comparison_bar_graph

multi_input_decoder_layout = html.Div(
    [
        card_wrapper(
            dbc.Row([dbc.Col(graph_wrapper(PATHNET_MID_PRED_SOURCE), width=4), dbc.Col(width=4), dbc.Col(width=4)])
        ),
        card_wrapper(
            dbc.Row(
                [
                    dbc.Col(graph_wrapper(PATHNET_MID_MATCHED_PRED_SOURCE_HOST), width=4),
                    dbc.Col(graph_wrapper(PATHNET_MID_MATCHED_PRED_SOURCE_NON_HOST), width=4),
                    dbc.Col(graph_wrapper(PATHNET_MID_MATCHED_PRED_SOURCE_ALL), width=4),
                ]
            )
        ),
        card_wrapper(
            dbc.Row(
                [
                    dbc.Col(graph_wrapper(PATHNET_MID_MATCHED_INPUT_SOURCE_HOST), width=4),
                    dbc.Col(graph_wrapper(PATHNET_MID_MATCHED_INPUT_SOURCE_NON_HOST), width=4),
                    dbc.Col(graph_wrapper(PATHNET_MID_MATCHED_INPUT_SOURCE_ALL), width=4),
                ]
            )
        ),
    ]
)


def get_pathnet_sources_df(
    data_tables, meta_data, meta_data_filters, pathnet_filters, source_column, graph_name, role=""
):
    query = generate_count_query(
        data_tables,
        meta_data,
        group_by_column=source_column,
        meta_data_filters=meta_data_filters,
        extra_filters=pathnet_filters,
        role=role,
        extra_columns=[source_column],
        group_by_net_id=True,
    )
    df, _ = run_query_with_nets_names_processing(query)
    df = df[~df["net_id"].str.endswith("sf") & ~df["net_id"].str.endswith("rem")]
    df = df.sort_values(by=["net_id", source_column]).dropna()
    df = df.rename(columns={"overall": "source_count"})
    total_counts = df.groupby("net_id")["source_count"].transform("sum")
    df["source_percent"] = (df["source_count"] / total_counts) * 100
    df["text"] = df.apply(lambda row: f"{row['source_count']}<br>{row['source_percent']:.1f}%", axis=1)
    df[source_column] = df[source_column].replace("fusion", "rem")

    return comparison_bar_graph(
        df,
        x="net_id",
        y="source_count",
        facet_col=source_column,
        title=f"{role if role else 'all'} {graph_name}".title(),
        text="text",
    )


@callback(
    Output(PATHNET_MID_MATCHED_PRED_SOURCE_HOST, "figure"),
    Output(PATHNET_MID_MATCHED_PRED_SOURCE_NON_HOST, "figure"),
    Output(PATHNET_MID_MATCHED_PRED_SOURCE_ALL, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
)
def get_pathnet_matched_pred_source_graphs(meta_data_filters, pathnet_filters, nets):
    if not nets:
        return no_update
    data_tables = nets["pathnet_gt_tables"]
    md = nets["meta_data"]

    args = [data_tables, md, meta_data_filters, pathnet_filters, "matched_source", "matched predictions source"]
    host_figure = get_pathnet_sources_df(*args, role="host")
    non_host_figure = get_pathnet_sources_df(*args, role="non-host")
    all_figure = get_pathnet_sources_df(*args)
    return host_figure, non_host_figure, all_figure


@callback(
    Output(PATHNET_MID_MATCHED_INPUT_SOURCE_HOST, "figure"),
    Output(PATHNET_MID_MATCHED_INPUT_SOURCE_NON_HOST, "figure"),
    Output(PATHNET_MID_MATCHED_INPUT_SOURCE_ALL, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
)
def get_pathnet_input_matching_graphs(meta_data_filters, pathnet_filters, nets):
    if not nets:
        return no_update

    data_tables = nets["pathnet_gt_tables"]
    md = nets["meta_data"]

    args = [data_tables, md, meta_data_filters, pathnet_filters, "matched_input_source", "matched inputs source"]
    host_figure = get_pathnet_sources_df(*args, role="host")
    non_host_figure = get_pathnet_sources_df(*args, role="non-host")
    all_figure = get_pathnet_sources_df(*args)
    return host_figure, non_host_figure, all_figure


@callback(
    Output(PATHNET_MID_PRED_SOURCE, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PATHNET_FILTERS, "data"),
    Input(NETS, "data"),
)
def get_pathnet_input_matching_graphs(meta_data_filters, pathnet_filters, nets):
    if not nets:
        return no_update

    data_tables = nets["pathnet_pred_tables"]
    md = nets["meta_data"]

    return get_pathnet_sources_df(data_tables, md, meta_data_filters, pathnet_filters, "source", "predictions source")
