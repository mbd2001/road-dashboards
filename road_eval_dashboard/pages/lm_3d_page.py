import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import html, dcc, register_page, Input, Output, callback, State, no_update, MATCH

from road_eval_dashboard.components import (
    meta_data_filter,
    base_dataset_statistics,
)
from road_eval_dashboard.components.common_filters import LM_3D_FILTERS
from road_eval_dashboard.components.components_ids import (
    MD_FILTERS,
    NETS, LM_3D_ACC_NEXT, LM_3D_ACC_HOST, LM_3D_ACC_OVERALL, LM_3D_ACC_OVERALL_Z_X, LM_3D_ACC_HOST_Z_X,
)
from road_eval_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper
from road_eval_dashboard.components.page_properties import PageProperties
from road_eval_dashboard.components.queries_manager import (
    run_query_with_nets_names_processing, lm_3d_distances, generate_lm_3d_query,
    INTERSTING_FILTERS_DIST_TO_CHECK,
)
from road_eval_dashboard.graphs.path_net_line_graph import draw_path_net_graph

extra_properties = PageProperties("line-chart")
register_page(__name__, path="/lm_3d", name="LM 3D", order=3, **extra_properties.__dict__)


def get_host_next_graph(host_id, next_id, is_Z_id):
    return card_wrapper(
        [
            dbc.Row(
                [
                    dbc.Col(
                        loading_wrapper([dcc.Graph(id=host_id, config={"displayModeBar": False})]),
                        width=6,
                    ),
                    dbc.Col(
                        loading_wrapper([dcc.Graph(id=next_id, config={"displayModeBar": False})]),
                        width=6,
                    ),
                ]
            ),
            daq.BooleanSwitch(
                id=is_Z_id,
                on=False,
                label="show by Z",
                labelPosition="top",
            ),
        ]
    )


layout = html.Div(
    [
        html.H1("Lane Mark 3D", className="mb-5"),
        meta_data_filter.layout,
        base_dataset_statistics.gt_layout,
        card_wrapper(
        [
                dbc.Row(
                    loading_wrapper([dcc.Graph(id=LM_3D_ACC_OVERALL, config={"displayModeBar": False})])),

                daq.BooleanSwitch(
                    id=LM_3D_ACC_OVERALL_Z_X,
                    on=False,
                    label="show by Z",
                    labelPosition="top",
                ),
        ]),
        get_host_next_graph({"type": LM_3D_ACC_HOST, "extra_filter": ""},
                             {"type": LM_3D_ACC_NEXT, "extra_filter": ""},
                             {"type": LM_3D_ACC_HOST_Z_X, "extra_filter": ""}),
    ] + [get_host_next_graph({"type": LM_3D_ACC_HOST, "extra_filter": filter_name},
                             {"type": LM_3D_ACC_NEXT, "extra_filter": filter_name},
                             {"type": LM_3D_ACC_HOST_Z_X, "extra_filter": filter_name}) for filter_name in LM_3D_FILTERS]
)


@callback(
    Output(LM_3D_ACC_OVERALL, "figure"),
    Input(MD_FILTERS, "data"),
    Input(LM_3D_ACC_OVERALL_Z_X, "on"),
    State(NETS, "data"),
    background=True,
)
def get_lm_3d_acc_overall(meta_data_filters, is_Z, nets):
    if not nets:
        return no_update

    query = generate_lm_3d_query(
        nets['gt_tables'],
        nets["meta_data"],
        "accuracy",
        meta_data_filters=meta_data_filters,
        is_Z=is_Z
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, lm_3d_distances, "accuracy", role="overall", hover=True)

@callback(
    Output({"type": LM_3D_ACC_HOST, "extra_filter": MATCH}, "figure"),
    Output({"type": LM_3D_ACC_NEXT, "extra_filter": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    Input({"type": LM_3D_ACC_HOST_Z_X, "extra_filter": MATCH}, "on"),
    State(NETS, "data"),
    State({"type": LM_3D_ACC_HOST, "extra_filter": MATCH}, 'id'),
    background=True,
)
def get_lm_3d_acc_interesting_filter(meta_data_filters, is_Z, nets, id):
    if not nets:
        return no_update

    extra_filter = id['extra_filter']
    intresting_filter = LM_3D_FILTERS[extra_filter] if extra_filter else None
    figs = []
    for role in ['host', 'next']:
        query = generate_lm_3d_query(
            nets['gt_tables'],
            nets["meta_data"],
            "accuracy",
            meta_data_filters=meta_data_filters,
            role=role,
            is_Z=is_Z,
            intresting_filters=intresting_filter
        )
        df, _ = run_query_with_nets_names_processing(query)
        cols_names = get_cols_names(intresting_filter)
        fig = draw_path_net_graph(df, cols_names, "accuracy", role=role, hover=True)
        figs.append(fig)
    return figs


def get_cols_names(intresting_filter):
    if intresting_filter:
        intresting_filter_names = list(intresting_filter.keys())
        return [f"{INTERSTING_FILTERS_DIST_TO_CHECK}_{col}" for col in intresting_filter_names]
    return lm_3d_distances