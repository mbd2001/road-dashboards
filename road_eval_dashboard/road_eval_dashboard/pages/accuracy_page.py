import dash_bootstrap_components as dbc
from dash import Input, Output, callback, html, no_update, register_page

from road_eval_dashboard.road_eval_dashboard.components import fb_meta_data_filters, meta_data_filter
from road_eval_dashboard.road_eval_dashboard.components.components_ids import FB_TRADEOFF_HOST, FB_TRADEOFF_OVERALL, MD_FILTERS, NETS
from road_eval_dashboard.road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_eval_dashboard.road_eval_dashboard.components.layout_wrapper import card_wrapper
from road_eval_dashboard.road_eval_dashboard.components.page_properties import PageProperties
from road_eval_dashboard.road_eval_dashboard.components.queries_manager import generate_fb_query, run_query_with_nets_names_processing
from road_eval_dashboard.road_eval_dashboard.components import base_dataset_statistics
from road_eval_dashboard.road_eval_dashboard.graphs import draw_precision_recall_curve

extra_properties = PageProperties("line-chart")
register_page(__name__, path="/accuracy", name="Accuracy", order=3, **extra_properties.__dict__)

layout = html.Div(
    [
        html.H1("Lane Mark Accuracy", className="mb-5"),
        meta_data_filter.layout,
        base_dataset_statistics.gt_layout,
        card_wrapper(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            graph_wrapper(FB_TRADEOFF_OVERALL),
                            width=6,
                        ),
                        dbc.Col(graph_wrapper(FB_TRADEOFF_HOST), width=6),
                    ]
                )
            ]
        ),
        fb_meta_data_filters.layout,
    ]
)


@callback(
    Output(FB_TRADEOFF_HOST, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
)
def get_fb_host(meta_data_filters, nets):
    if not nets:
        return no_update

    query = generate_fb_query(
        nets["gt_tables"], nets["pred_tables"], nets["meta_data"], meta_data_filters=meta_data_filters, role="host"
    )
    data, _ = run_query_with_nets_names_processing(query)
    data = data.fillna(1)
    return draw_precision_recall_curve(data, "host")


@callback(
    Output(FB_TRADEOFF_OVERALL, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
)
def get_fb_overall(meta_data_filters, nets):
    if not nets:
        return no_update

    query = generate_fb_query(
        nets["gt_tables"], nets["pred_tables"], nets["meta_data"], meta_data_filters=meta_data_filters
    )
    data, _ = run_query_with_nets_names_processing(query)
    data = data.fillna(1)
    return draw_precision_recall_curve(data, "overall")
