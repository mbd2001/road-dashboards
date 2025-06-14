import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import MATCH, Input, Output, State, callback, dcc, html, no_update, register_page

from road_dashboards.road_eval_dashboard.components import base_dataset_statistics, meta_data_filter
from road_dashboards.road_eval_dashboard.components.common_filters import LM_3D_FILTERS
from road_dashboards.road_eval_dashboard.components.components_ids import (
    EFFECTIVE_SAMPLES_PER_BATCH,
    LM_3D_ACC_HOST,
    LM_3D_ACC_HOST_Z_X,
    LM_3D_ACC_NEXT,
    LM_3D_ACC_OVERALL,
    LM_3D_ACC_OVERALL_Z_X,
    LM_3D_AVG_ERROR_HOST,
    LM_3D_AVG_ERROR_NEXT,
    LM_3D_AVG_ERROR_Z_X,
    LM_3D_SOURCE_DROPDOWN,
    MD_FILTERS,
    NETS,
)
from road_dashboards.road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_dashboards.road_eval_dashboard.components.layout_wrapper import card_wrapper
from road_dashboards.road_eval_dashboard.components.page_properties import PageProperties
from road_dashboards.road_eval_dashboard.components.queries_manager import (
    ZSources,
    generate_lm_3d_query,
    generate_sum_bins_by_diff_cols_metric_query,
    lm_3d_distances,
    lm_3D_sec_to_X_dist_acc,
    run_query_with_nets_names_processing,
)
from road_dashboards.road_eval_dashboard.graphs.meta_data_filters_graph import draw_meta_data_filters
from road_dashboards.road_eval_dashboard.graphs.path_net_line_graph import draw_path_net_graph
from road_dashboards.road_eval_dashboard.pages.card_generators import get_host_next_graph

extra_properties = PageProperties("line-chart")
register_page(__name__, path="/lm_3d", name="LM 3D", order=3, **extra_properties.__dict__)


def get_3d_source_layout():
    options = [s.value for s in ZSources if s != ZSources.Z_COORDS]
    return card_wrapper(
        [
            html.H6("Choose 3d source"),
            dcc.Dropdown(options, ZSources.FUSION, id=LM_3D_SOURCE_DROPDOWN),
        ]
    )


layout = html.Div(
    [
        html.H1("Lane Mark 3D", className="mb-5"),
        meta_data_filter.layout,
        base_dataset_statistics.gt_layout,
        get_3d_source_layout(),
        card_wrapper(
            [
                dbc.Row([graph_wrapper(LM_3D_ACC_OVERALL)]),
                daq.BooleanSwitch(
                    id=LM_3D_ACC_OVERALL_Z_X,
                    on=False,
                    label="show by Z",
                    labelPosition="top",
                ),
            ]
        ),
        get_host_next_graph(
            {"type": LM_3D_AVG_ERROR_HOST, "extra_filter": ""},
            {"type": LM_3D_AVG_ERROR_NEXT, "extra_filter": ""},
            {"type": LM_3D_AVG_ERROR_Z_X, "extra_filter": ""},
        ),
        get_host_next_graph(
            {"type": LM_3D_ACC_HOST, "extra_filter": ""},
            {"type": LM_3D_ACC_NEXT, "extra_filter": ""},
            {"type": LM_3D_ACC_HOST_Z_X, "extra_filter": ""},
        ),
    ]
    + [
        get_host_next_graph(
            {"type": LM_3D_ACC_HOST, "extra_filter": filter_name},
            {"type": LM_3D_ACC_NEXT, "extra_filter": filter_name},
            {"type": LM_3D_ACC_HOST_Z_X, "extra_filter": filter_name},
        )
        for filter_name in LM_3D_FILTERS
    ]
)


def get_labels_to_preds_with_names(source, Z_or_X):
    labels_to_preds = {}
    axis = "Z" if Z_or_X else "X"
    base_column_name = f"pos_dZ_{source}_{axis}_dists"
    for sec in lm_3D_sec_to_X_dist_acc:
        col_name = f"{base_column_name}_{sec}"
        labels_to_preds[str(sec)] = (col_name, col_name)
    return labels_to_preds


@callback(
    Output({"type": LM_3D_AVG_ERROR_HOST, "extra_filter": ""}, "figure"),
    Output({"type": LM_3D_AVG_ERROR_NEXT, "extra_filter": ""}, "figure"),
    Input({"type": LM_3D_AVG_ERROR_Z_X, "extra_filter": ""}, "value"),
    Input(LM_3D_SOURCE_DROPDOWN, "value"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
)
def get_average_error_graph(Z_or_X, source, meta_data_filters, nets, effective_samples):
    labels_to_preds = get_labels_to_preds_with_names(source, Z_or_X)
    figs = []
    for role in ["host", "next"]:
        query = generate_sum_bins_by_diff_cols_metric_query(
            nets["gt_tables"],
            nets["meta_data"],
            labels_to_preds=labels_to_preds,
            meta_data_filters=meta_data_filters,
            role=role,
            is_count_lm=True,
        )
        data, _ = run_query_with_nets_names_processing(query)
        data = data.sort_values(by="net_id")
        for sec in lm_3D_sec_to_X_dist_acc:
            data[f"score_{sec}"] = data[f"score_{sec}"] / data[f"count_{sec}"]
        fig = draw_meta_data_filters(
            data,
            list(labels_to_preds.keys()),
            get_lm_3d_score,
            effective_samples=effective_samples,
            title=f"Average Error By {source}",
            xaxis="Sec",
            yaxis="Avg Error",
            hover=True,
        )
        figs.append(fig)
    return figs


@callback(
    Output(LM_3D_ACC_OVERALL, "figure"),
    Input(MD_FILTERS, "data"),
    Input(LM_3D_ACC_OVERALL_Z_X, "on"),
    Input(LM_3D_SOURCE_DROPDOWN, "value"),
    Input(NETS, "data"),
)
def get_lm_3d_acc_overall(meta_data_filters, is_Z, Z_source, nets):
    if not nets:
        return no_update

    query = generate_lm_3d_query(
        nets["gt_tables"],
        nets["meta_data"],
        "accuracy",
        meta_data_filters=meta_data_filters,
        is_Z=is_Z,
        Z_source=Z_source,
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, lm_3d_distances, "accuracy", role="overall", hover=True)


@callback(
    Output({"type": LM_3D_ACC_HOST, "extra_filter": MATCH}, "figure", allow_duplicate=True),
    Output({"type": LM_3D_ACC_NEXT, "extra_filter": MATCH}, "figure", allow_duplicate=True),
    Input(MD_FILTERS, "data"),
    Input({"type": LM_3D_ACC_HOST_Z_X, "extra_filter": MATCH}, "on"),
    Input(LM_3D_SOURCE_DROPDOWN, "value"),
    Input(NETS, "data"),
    State({"type": LM_3D_ACC_HOST, "extra_filter": MATCH}, "id"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    prevent_initial_call=True,
)
def get_lm_3d_acc_interesting_filter(meta_data_filters, is_Z, Z_source, nets, graph_id, effective_samples):
    if not nets:
        return no_update

    extra_filter = graph_id["extra_filter"]
    intresting_filter = LM_3D_FILTERS[extra_filter] if extra_filter else None
    if intresting_filter is None:
        effective_samples = {}
    figs = []
    for role in ["host", "next"]:
        query = generate_lm_3d_query(
            nets["gt_tables"],
            nets["meta_data"],
            "accuracy",
            meta_data_filters=meta_data_filters,
            role=role,
            is_Z=is_Z,
            intresting_filters=intresting_filter,
            Z_source=Z_source,
        )
        df, _ = run_query_with_nets_names_processing(query)
        cols_names = get_cols_names(intresting_filter)
        fig = draw_path_net_graph(
            df, cols_names, "accuracy", role=role, hover=True, effective_samples=effective_samples
        )
        figs.append(fig)
    return figs


def get_cols_names(intresting_filter):
    if intresting_filter:
        intresting_filter_names = list(intresting_filter.keys())
        return [col for col in intresting_filter_names]
    return lm_3d_distances


def get_lm_3d_score(row, filter_name):
    score = row[f"score_{filter_name}"]
    return score
