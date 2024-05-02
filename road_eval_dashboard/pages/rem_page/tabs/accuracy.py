import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import MATCH, Input, Output, State, callback, dcc, html, no_update

from road_eval_dashboard.components.components_ids import (
    EFFECTIVE_SAMPLES_PER_BATCH,
    MD_FILTERS,
    NETS,
    REM_ACCURACY_3D_SOURCE_DROPDOWN,
    REM_ACCURACY_ERROR_THRESHOLD_SLIDER,
    REM_ERROR_HISTOGRAM,
    REM_ERROR_HISTOGRAM_Z_OR_SEC,
    REM_ROLES_DROPDOWN,
)
from road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_eval_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper
from road_eval_dashboard.components.queries_manager import (
    ZSources,
    generate_sum_bins_metric_query,
    run_query_with_nets_names_processing,
)
from road_eval_dashboard.graphs.meta_data_filters_graph import draw_meta_data_filters
from road_eval_dashboard.pages.rem_page.utils import (
    IGNORES_FILTER,
    REM_FILTERS,
    REM_TYPE,
    SEC_FILTERS,
    Z_FILTERS,
    get_base_graph_layout,
    get_rem_fig,
    get_rem_score,
)

TAB = "accuracy"


def get_settings_layout():
    options = [s.value for s in ZSources]
    return card_wrapper(
        [
            html.H6("Choose 3d source"),
            dcc.Dropdown(options, ZSources.FUSION, id=REM_ACCURACY_3D_SOURCE_DROPDOWN),
            html.H6("Choose Error Threshold", style={"margin-top": 10}),
            html.Div(
                [
                    dcc.Slider(
                        id=REM_ACCURACY_ERROR_THRESHOLD_SLIDER,
                        min=0,
                        max=2,
                        step=0.2,
                        value=0.2,
                    ),
                ],
                style={"margin-top": 5},
            ),
        ]
    )


def get_error_histogram_layout():
    return card_wrapper(
        [
            dbc.Row(
                graph_wrapper(
                           REM_ERROR_HISTOGRAM,
                )
            ),
            dbc.Stack(
                [
                    daq.BooleanSwitch(
                        id=REM_ERROR_HISTOGRAM_Z_OR_SEC,
                        on=False,
                        label="Sec/Z",
                        labelPosition="top",
                        persistence=True,
                        persistence_type="session",
                    )
                ],
                direction="horizontal",
                gap=3,
            ),
        ]
    )


layout = html.Div(
    [get_settings_layout(), get_error_histogram_layout()]
    + [
        get_base_graph_layout(filter_name, TAB, sort_by_dist=filter_props.get("sort_by_dist", False))
        for filter_name, filter_props in REM_FILTERS.items()
    ]
)


@callback(
    Output(REM_ERROR_HISTOGRAM, "figure"),
    Input(REM_ROLES_DROPDOWN, "value"),
    Input(REM_ACCURACY_3D_SOURCE_DROPDOWN, "value"),
    Input(REM_ERROR_HISTOGRAM_Z_OR_SEC, "on"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
)
def get_error_histogram_graph(role, source, z_or_sec, meta_data_filters, nets, effective_samples):
    sum_col = f"rem_accuracy_{source}"
    interesting_filters = Z_FILTERS if z_or_sec else SEC_FILTERS
    query = generate_sum_bins_metric_query(
        nets["gt_tables"],
        nets["meta_data"],
        sum_col=sum_col,
        interesting_filters=interesting_filters,
        meta_data_filters=meta_data_filters,
        extra_filters=IGNORES_FILTER.format(col=sum_col),
        extra_columns=["rem_point_sec", "rem_point_Z"],
        role=role,
    )
    data, _ = run_query_with_nets_names_processing(query)
    data = data.sort_values(by="net_id")
    fig = draw_meta_data_filters(
        data,
        list(interesting_filters.keys()),
        get_rem_score,
        effective_samples=effective_samples,
        title=f"Error Histogram By {source}",
        yaxis="Score",
        hover=True,
    )
    return fig


@callback(
    Output({"out": "graph", "filter": MATCH, "rem_type": REM_TYPE, "sort_by_dist": False, "tab": TAB}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(REM_ROLES_DROPDOWN, "value"),
    Input(REM_ACCURACY_3D_SOURCE_DROPDOWN, "value"),
    Input(REM_ACCURACY_ERROR_THRESHOLD_SLIDER, "value"),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    State({"out": "graph", "filter": MATCH, "rem_type": REM_TYPE, "sort_by_dist": False, "tab": TAB}, "id"),
    background=True,
)
def get_none_dist_graph(meta_data_filters, role, source, error_threshold, nets, effective_samples, graph_id):
    if not nets:
        return no_update
    filter_name = graph_id["filter"]
    filters = REM_FILTERS[filter_name]
    interesting_filters = filters["filters"]
    fig = get_accuracy_fig(
        meta_data_filters=meta_data_filters,
        nets=nets,
        interesting_filters=interesting_filters,
        effective_samples=effective_samples,
        filter_name=filter_name,
        source=source,
        error_threshold=error_threshold,
        role=role,
    )
    return fig


@callback(
    Output({"out": "graph", "filter": MATCH, "rem_type": REM_TYPE, "sort_by_dist": True, "tab": TAB}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(REM_ROLES_DROPDOWN, "value"),
    Input(REM_ACCURACY_3D_SOURCE_DROPDOWN, "value"),
    Input(REM_ACCURACY_ERROR_THRESHOLD_SLIDER, "value"),
    Input({"out": "sort_by_dist", "filter": MATCH, "rem_type": REM_TYPE, "sort_by_dist": True, "tab": TAB}, "on"),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    State({"out": "graph", "filter": MATCH, "rem_type": REM_TYPE, "sort_by_dist": True, "tab": TAB}, "id"),
    background=True,
)
def get_dist_graph(meta_data_filters, role, source, error_threshold, sort_by_dist, nets, effective_samples, graph_id):
    if not nets:
        return no_update
    filter_name = graph_id["filter"]
    filters = REM_FILTERS[filter_name]
    interesting_filters = filters["dist_filters"] if sort_by_dist else filters["filters"]
    fig = get_accuracy_fig(
        meta_data_filters=meta_data_filters,
        nets=nets,
        interesting_filters=interesting_filters,
        effective_samples=effective_samples,
        filter_name=filter_name,
        source=source,
        error_threshold=error_threshold,
        role=role,
    )
    return fig


def get_accuracy_fig(
    meta_data_filters, nets, interesting_filters, effective_samples, filter_name, source, error_threshold, role=""
):
    label = f"rem_accuracy_{source}"
    pred = error_threshold
    title = f"Accuracy By {source} With Threshold {error_threshold}"
    fig = get_rem_fig(
        meta_data_filters, nets, interesting_filters, effective_samples, filter_name, title, label, pred, role=role
    )
    return fig
