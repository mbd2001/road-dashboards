import pandas as pd
import plotly.express as px
from dash import MATCH, Input, Output, State, callback, html, no_update, register_page

from road_eval_dashboard.road_eval_dashboard.components import meta_data_filter
from road_eval_dashboard.road_eval_dashboard.components.components_ids import (
    EFFECTIVE_SAMPLES_PER_BATCH,
    MD_FILTERS,
    NETS,
    VIEW_RANGE_HISTOGRAM,
    VIEW_RANGE_HISTOGRAM_BIN_SIZE_SLIDER,
    VIEW_RANGE_HISTOGRAM_CUMULATIVE,
    VIEW_RANGE_HISTOGRAM_ERR_EST,
    VIEW_RANGE_HISTOGRAM_ERR_EST_THRESHOLD,
    VIEW_RANGE_HISTOGRAM_NAIVE_Z,
    VIEW_RANGE_SUCCESS_RATE,
    VIEW_RANGE_SUCCESS_RATE_ERR_EST,
    VIEW_RANGE_SUCCESS_RATE_ERR_EST_THRESHOLD,
    VIEW_RANGE_SUCCESS_RATE_HOST_NEXT,
    VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_ERR_EST,
    VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_ERR_EST_THRESHOLD,
    VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_NAIVE_Z,
    VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_Z_RANGE,
    VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_Z_STEP,
    VIEW_RANGE_SUCCESS_RATE_NAIVE_Z,
    VIEW_RANGE_SUCCESS_RATE_Z_RANGE,
    VIEW_RANGE_SUCCESS_RATE_Z_STEP,
)
from road_eval_dashboard.road_eval_dashboard.components.page_properties import PageProperties
from road_eval_dashboard.road_eval_dashboard.components.queries_manager import (
    generate_view_range_histogram_query,
    generate_view_range_success_rate_query,
    get_view_range_col_name,
    run_query_with_nets_names_processing,
)
from road_eval_dashboard.road_eval_dashboard.pages.card_generators import (
    view_range_histogram_card,
    view_range_host_next_success_rate_card,
    view_range_success_rate_card,
)
from road_eval_dashboard.road_eval_dashboard.components import base_dataset_statistics

extra_properties = PageProperties("line-chart")
register_page(__name__, path="/lm_view_range", name="LM View Range", order=3, **extra_properties.__dict__)


def melt_df_by_metric(df: pd.DataFrame, metric: str):
    df_melted = pd.melt(
        df,
        id_vars=["net_id"],
        var_name="Z_sample",
        value_name=metric,
        value_vars=[c for c in df.columns if c.startswith(metric)],
    )
    df_melted["Z_sample"] = df_melted["Z_sample"].str.extract("(\d+)").astype(int)
    return df_melted


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
    Input(VIEW_RANGE_SUCCESS_RATE_ERR_EST, "on"),
    Input(VIEW_RANGE_SUCCESS_RATE_Z_RANGE, "value"),
    Input(VIEW_RANGE_SUCCESS_RATE_Z_STEP, "value"),
    Input(VIEW_RANGE_SUCCESS_RATE_ERR_EST_THRESHOLD, "value"),
    Input(NETS, "data"),
)
def get_view_range_success_rate_plot(
    meta_data_filters, naive_Z, filter_err_est, Z_range, Z_step, err_est_threshold, nets
):
    if not nets:
        return no_update
    Z_samples = list(range(Z_range[0], Z_range[1] + 1, Z_step))
    query = generate_view_range_success_rate_query(
        nets["gt_tables"],
        nets["meta_data"],
        Z_samples=Z_samples,
        meta_data_filters=meta_data_filters,
        naive_Z=naive_Z,
        use_err_est=filter_err_est,
        err_est_threshold=err_est_threshold,
    )
    df, _ = run_query_with_nets_names_processing(query)
    df_melted_score = melt_df_by_metric(df, "vr_score")
    df_melted_num_gt = melt_df_by_metric(df, "vr_num_gt")
    merged_df = pd.merge(df_melted_score, df_melted_num_gt, on=["net_id", "Z_sample"])
    merged_df["vr_num_gt"] = merged_df["vr_num_gt"].astype(int)
    merged_df.sort_values(by=["net_id", "Z_sample"], inplace=True)
    fig = px.line(
        merged_df,
        x="Z_sample",
        y="vr_score",
        markers=True,
        color="net_id",
        hover_data={"Z_sample": True, "net_id": False, "vr_num_gt": True, "vr_score": True},
        labels={"vr_score": "score", "vr_num_gt": "Num GT", "Z_sample": "Z"},
    )
    fig.update_xaxes(tickvals=Z_samples)
    fig.update_layout(
        title=f"<b>View Range Success Rate<b>",
        xaxis_title="Z(m)",
        yaxis_title="Success Rate",
        xaxis=dict(constrain="domain"),
        yaxis=dict(range=[0, 1]),
        font=dict(size=16),
        hoverlabel=dict(font_size=16),
    )
    return fig


@callback(
    Output({"type": VIEW_RANGE_SUCCESS_RATE_HOST_NEXT, "extra_filter": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    Input({"type": VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_NAIVE_Z, "extra_filter": MATCH}, "on"),
    Input({"type": VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_ERR_EST, "extra_filter": MATCH}, "on"),
    Input({"type": VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_Z_RANGE, "extra_filter": MATCH}, "value"),
    Input({"type": VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_Z_STEP, "extra_filter": MATCH}, "value"),
    Input({"type": VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_ERR_EST_THRESHOLD, "extra_filter": MATCH}, "value"),
    Input(NETS, "data"),
    State({"type": VIEW_RANGE_SUCCESS_RATE_HOST_NEXT, "extra_filter": MATCH}, "id"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
)
def get_view_range_success_rate_interesting_plots(
    meta_data_filters, naive_Z, filter_err_est, Z_range, Z_step, err_est_threshold, nets, id, effective_samples
):
    if not nets:
        return no_update

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
            use_err_est=filter_err_est,
            err_est_threshold=err_est_threshold,
        )

        df, _ = run_query_with_nets_names_processing(query)
        df_melted_score = melt_df_by_metric(df, "vr_score")
        df_melted_num_gt = melt_df_by_metric(df, "vr_num_gt")
        merged_df = pd.merge(df_melted_score, df_melted_num_gt, on=["net_id", "Z_sample"])
        merged_df["role"] = role
        dfs.append(merged_df)
    full_df = pd.concat(dfs)
    full_df["vr_num_gt"] = full_df["vr_num_gt"].astype(int)
    full_df.sort_values(by=["net_id", "Z_sample"], inplace=True)
    fig = px.line(
        full_df,
        x="Z_sample",
        y="vr_score",
        color="net_id",
        facet_col="role",
        markers=True,
        hover_data={"Z_sample": True, "net_id": False, "role": False, "vr_num_gt": True, "vr_score": True},
        labels={"vr_score": "score", "vr_num_gt": "Num GT", "Z_sample": "Z"},
    )
    fig.update_xaxes(tickvals=Z_samples)
    fig.update_yaxes(range=[0, 1])
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig.update_layout(
        title=f"<b>View Range Success Rate - Host & Next<b>",
        xaxis_title="Z(m)",
        yaxis_title="Success Rate",
        xaxis=dict(constrain="domain"),
        yaxis=dict(range=[0, 1]),
        font=dict(size=16),
        hoverlabel=dict(font_size=16),
    )
    return fig


@callback(
    Output(VIEW_RANGE_HISTOGRAM, "figure", allow_duplicate=True),
    Input(MD_FILTERS, "data"),
    Input(VIEW_RANGE_HISTOGRAM_BIN_SIZE_SLIDER, "value"),
    Input(VIEW_RANGE_HISTOGRAM_NAIVE_Z, "on"),
    Input(VIEW_RANGE_HISTOGRAM_ERR_EST, "on"),
    Input(VIEW_RANGE_HISTOGRAM_CUMULATIVE, "on"),
    Input(VIEW_RANGE_HISTOGRAM_ERR_EST_THRESHOLD, "value"),
    Input(NETS, "data"),
    prevent_initial_call=True,
)
def get_view_range_histogram_plot(
    meta_data_filters, bin_size, naive_Z, filter_err_est, cumulative_graph, err_est_threshold, nets
):
    if not nets:
        return no_update
    xaxis_direction = None
    query = generate_view_range_histogram_query(
        nets["gt_tables"],
        nets["meta_data"],
        bin_size=bin_size,
        meta_data_filters=meta_data_filters,
        naive_Z=naive_Z,
        use_err_est=filter_err_est,
        err_est_threshold=err_est_threshold,
    )
    df, _ = run_query_with_nets_names_processing(query)
    max_Z_col = get_view_range_col_name("view_range_max_Z", naive_Z, filter_err_est, err_est_threshold)
    df.loc[pd.isna(df[f"{max_Z_col}_pred"]), "overall"] = 0
    if cumulative_graph:
        cumsum_df = df.groupby(["net_id", f"{max_Z_col}_pred"]).sum()[::-1].groupby(level=0).cumsum().reset_index()
        cumsum_df = cumsum_df.sort_values(["net_id", f"{max_Z_col}_pred"], ascending=False).reset_index()
        df = df.sort_values(["net_id", f"{max_Z_col}_pred"], ascending=False).reset_index()
        cumsum_df["score"] = cumsum_df["overall"] / df.groupby(["net_id"])["overall"].transform("sum")
        df = cumsum_df
        xaxis_direction = "reversed"
    else:
        df["score"] = df["overall"]
    df.sort_values(by=["net_id", f"{max_Z_col}_pred"], inplace=True)
    fig = px.line(
        df,
        x=f"{max_Z_col}_pred",
        y="score",
        color="net_id",
        markers=True,
        hover_data={f"{max_Z_col}_pred": True, "net_id": False, "overall": True},
        labels={
            f"{max_Z_col}_pred": "Z",
            "overall": "Count",
        },
    )
    fig.update_layout(
        title=f"<b>View Range Histogram<b>",
        xaxis_title="Z(m)",
        yaxis_title="Count",
        font=dict(size=16),
        hoverlabel=dict(font_size=16),
        xaxis=dict(autorange=xaxis_direction),
    )
    return fig
