import dash_bootstrap_components as dbc
from dash import html, dcc, register_page, Input, Output, callback, State, no_update

from road_eval_dashboard.components import (
    meta_data_filter,
    base_dataset_statistics,
)
from road_eval_dashboard.components.components_ids import (
    MD_FILTERS,
    NETS, LM_3D_ACC_NEXT, LM_3D_ACC_HOST, LM_3D_ACC_OVERALL,
)
from road_eval_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper
from road_eval_dashboard.components.page_properties import PageProperties
from road_eval_dashboard.components.queries_manager import (
    run_query_with_nets_names_processing, generate_path_net_query, lm_3d_distances, generate_lm_3d_query,
)
from road_eval_dashboard.graphs.path_net_line_graph import draw_path_net_graph

extra_properties = PageProperties("line-chart")
register_page(__name__, path="/lm_3d", name="LM 3D", order=3, **extra_properties.__dict__)

layout = html.Div(
    [
        html.H1("Lane Mark 3D", className="mb-5"),
        meta_data_filter.layout,
        base_dataset_statistics.gt_layout,
        card_wrapper(
        [
                dbc.Row(
                    loading_wrapper([dcc.Graph(id=LM_3D_ACC_OVERALL, config={"displayModeBar": False})]))
        ]),
        card_wrapper(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            loading_wrapper([dcc.Graph(id=LM_3D_ACC_HOST, config={"displayModeBar": False})]),
                            width=6,
                        ),
                        dbc.Col(
                            loading_wrapper([dcc.Graph(id=LM_3D_ACC_NEXT, config={"displayModeBar": False})]),
                            width=6,
                        ),
                    ]
                )
            ]
        ),
    ]
)


@callback(
    Output(LM_3D_ACC_OVERALL, "figure"),
    Input(MD_FILTERS, "data"),
    State(NETS, "data"),
    background=True,
)
def get_lm_3d_acc_overall(meta_data_filters, nets):
    if not nets:
        return no_update

    query = generate_lm_3d_query(
        nets['gt_tables'],
        nets["meta_data"],
        "accuracy",
        meta_data_filters=meta_data_filters,
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, lm_3d_distances, "accuracy", role="overall")

@callback(
    Output(LM_3D_ACC_HOST, "figure"),
    Input(MD_FILTERS, "data"),
    State(NETS, "data"),
    background=True,
)
def get_lm_3d_acc_host(meta_data_filters, nets):
    if not nets:
        return no_update

    query = generate_lm_3d_query(
        nets['gt_tables'],
        nets["meta_data"],
        "accuracy",
        meta_data_filters=meta_data_filters,
        role="host",
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, lm_3d_distances, "accuracy", role="host")


@callback(
    Output(LM_3D_ACC_NEXT, "figure"),
    Input(MD_FILTERS, "data"),
    State(NETS, "data"),
    background=True,
)
def get_lm_3d_acc_next(meta_data_filters, nets):
    if not nets:
        return no_update

    query = generate_lm_3d_query(
        nets['gt_tables'],
        nets["meta_data"],
        "accuracy",
        meta_data_filters=meta_data_filters,
        role="next",
    )
    df, _ = run_query_with_nets_names_processing(query)
    return draw_path_net_graph(df, lm_3d_distances, "accuracy")