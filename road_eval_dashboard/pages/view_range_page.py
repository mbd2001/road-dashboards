import pandas as pd
import plotly.express as px
from dash import MATCH, Input, Output, State, callback, html, no_update, register_page

from road_eval_dashboard.components import base_dataset_statistics, meta_data_filter
from road_eval_dashboard.components.components_ids import (
    EFFECTIVE_SAMPLES_PER_BATCH,
    MD_FILTERS,
    NETS,
    VIEW_RANGE_HISTOGRAM,
    VIEW_RANGE_HISTOGRAM_BIN_SIZE_SLIDER,
    VIEW_RANGE_SUCCESS_RATE,
    VIEW_RANGE_SUCCESS_RATE_HOST_NEXT,
    VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_NAIVE_Z,
    VIEW_RANGE_SUCCESS_RATE_NAIVE_Z, VIEW_RANGE_HISTOGRAM_NAIVE_Z, VIEW_RANGE_SUCCESS_RATE_Z_RANGE,
    VIEW_RANGE_SUCCESS_RATE_Z_STEP, VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_Z_RANGE, VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_Z_STEP,
)
from road_eval_dashboard.components.page_properties import PageProperties
from road_eval_dashboard.components.queries_manager import (
    generate_view_range_histogram_query,
    generate_view_range_success_rate_query,
    run_query_with_nets_names_processing,
)
from road_eval_dashboard.pages.card_generators import (
    view_range_histogram_card,
    view_range_host_next_success_rate_card,
    view_range_success_rate_card,
)

extra_properties = PageProperties("line-chart")
register_page(__name__, path="/lm_view_range", name="LM View Range", order=3, **extra_properties.__dict__)

layout = html.Div(
    [
        html.H1("Lane Mark View Range", className="mb-5"),
        meta_data_filter.layout,
        base_dataset_statistics.gt_layout,
        view_range_success_rate_card(),
        view_range_host_next_success_rate_card(),
        view_range_histogram_card(),
    ]
)


@callback(
    Output(VIEW_RANGE_SUCCESS_RATE, "figure"),
    Input(MD_FILTERS, "data"),
    Input(VIEW_RANGE_SUCCESS_RATE_NAIVE_Z, "on"),
    Input(VIEW_RANGE_SUCCESS_RATE_Z_RANGE, "value"),
    Input(VIEW_RANGE_SUCCESS_RATE_Z_STEP, "value"),
    State(NETS, "data"),
    background=True,
)
def get_view_range_success_rate_plot(meta_data_filters, naive_Z, Z_range, Z_step, nets):
    if not nets:
        return no_update
    Z_samples = list(range(Z_range[0], Z_range[1] + 1, Z_step))
    query = generate_view_range_success_rate_query(
        nets["gt_tables"],
        nets["meta_data"],
        Z_samples=Z_samples,
        meta_data_filters=meta_data_filters,
        naive_Z=naive_Z,
        # is_Z=is_Z
    )
    df, _ = run_query_with_nets_names_processing(query)
    df_melted = pd.melt(df, id_vars=["net_id"], var_name="Z_sample", value_name="vr_score")
    df_melted["Z_sample"] = df_melted["Z_sample"].str.extract("(\d+)").astype(int)
    df_melted.sort_values(by=["net_id", "Z_sample"], inplace=True)
    fig = px.line(
        df_melted,
        x="Z_sample",
        y="vr_score",
        labels={"Z_sample": "Z_sample", "vr_score": "vr_score"},
        markers=True,
        color="net_id",
    )
    fig.update_xaxes(tickvals=Z_samples)
    fig.update_layout(
        title=f"<b>View Range Success Rate<b>",
        xaxis_title="Z(m)",
        yaxis_title="Success Rate",
        xaxis=dict(constrain="domain"),
        yaxis=dict(range=[0, 1]),
        font=dict(size=16),
    )
    return fig


@callback(
    Output({"type": VIEW_RANGE_SUCCESS_RATE_HOST_NEXT, "extra_filter": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    Input({"type": VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_NAIVE_Z, "extra_filter": MATCH}, "on"),
    Input(VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_Z_RANGE, "value"),
    Input(VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_Z_STEP, "value"),
    State(NETS, "data"),
    State({"type": VIEW_RANGE_SUCCESS_RATE_HOST_NEXT, "extra_filter": MATCH}, "id"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    background=True,
)
def get_view_range_success_rate_interesting_plots(meta_data_filters, naive_Z, Z_range, Z_step, nets, id, effective_samples):
    if not nets:
        return no_update

    # extra_filter = id['extra_filter']
    # interesting_filters = VR_FILTERS[extra_filter] if extra_filter else None
    # if interesting_filters is None:
    #     effective_samples = {}

    #################
    Z_samples = list(range(Z_range[0], Z_range[1] + 1, Z_step))
    dfs = []
    for col, role in enumerate(["host", "next"]):
        query = generate_view_range_success_rate_query(
            nets["gt_tables"],
            nets["meta_data"],
            Z_samples=Z_samples,
            meta_data_filters=meta_data_filters,
            role=role,
            naive_Z=naive_Z,
        )

        df, _ = run_query_with_nets_names_processing(query)
        df_melted = pd.melt(df, id_vars=["net_id"], var_name="Z_sample", value_name="vr_score")
        df_melted["Z_sample"] = df_melted["Z_sample"].str.extract("(\d+)").astype(int)
        df_melted.sort_values(by=["net_id", "Z_sample"], inplace=True)
        df_melted["role"] = role
        dfs.append(df_melted)
    full_df = pd.concat(dfs)
    fig = px.line(full_df, x="Z_sample", y="vr_score", color="net_id", facet_col="role", markers=True)
    fig.update_xaxes(tickvals=Z_samples)
    fig.update_yaxes(range=[0, 1])
    return fig

    # fig.update_layout(
    #     title=f"<b>View Range Success Rate - {role.title()}<b>",
    #     xaxis_title="Z(m)",
    #     yaxis_title="Success Rate",
    #     xaxis=dict(constrain="domain"),
    #     yaxis=dict(range=[0, 1]),
    #     font=dict(size=16),
    # )
    # cols_names = get_cols_names(interesting_filters)
    # fig = draw_path_net_graph(df, cols_names, "accuracy", role=role, hover=True, effective_samples=effective_samples)
    ###################


@callback(
    Output(VIEW_RANGE_HISTOGRAM, "figure", allow_duplicate=True),
    Input(MD_FILTERS, "data"),
    Input(VIEW_RANGE_HISTOGRAM_BIN_SIZE_SLIDER, "value"),
    Input(VIEW_RANGE_HISTOGRAM_NAIVE_Z, "on"),
    State(NETS, "data"),
    background=True,
    prevent_initial_call=True,
)
def get_view_range_histogram_plot(meta_data_filters, bin_size, naive_Z, nets):
    if not nets:
        return no_update

    query = generate_view_range_histogram_query(
        nets["gt_tables"],
        nets["meta_data"],
        bin_size=bin_size,
        meta_data_filters=meta_data_filters,
        naive_Z=naive_Z,
    )
    df, _ = run_query_with_nets_names_processing(query)
    max_Z_col = "view_range_max_Z"
    if not naive_Z:
        max_Z_col += "_3d"
    df.sort_values(by=["net_id", f"{max_Z_col}_pred"], inplace=True)
    fig = px.line(df, x=f"{max_Z_col}_pred", y="overall", color="net_id", markers=True)
    # df2, _ = run_query_with_nets_names_processing(q)
    # fig = px.histogram(df2, x="view_range_max_Z_3d_pred", color="net_id", marginal="violin", nbins=bin_size)
    # fig.update_xaxes(tickvals=Z_SAMPLES)
    # fig.update_layout(
    #     title=f"<b>View Range Success Rate<b>",
    #     xaxis_title="Z(m)",
    #     yaxis_title="Success Rate",
    #     xaxis=dict(constrain="domain"),
    #     yaxis=dict(range=[0, 1]),
    #     font=dict(size=16),
    # )
    return fig
