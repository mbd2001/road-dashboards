from dash import MATCH, Input, Output, State, callback, dcc, html, no_update

from road_eval_dashboard.components.components_ids import (
    EFFECTIVE_SAMPLES_PER_BATCH,
    MD_FILTERS,
    NETS,
    REM_ACCURACY_3D_SOURCE_DROPDOWN,
    REM_ACCURACY_ERROR_THRESHOLD_SLIDER,
)
from road_eval_dashboard.components.layout_wrapper import card_wrapper
from road_eval_dashboard.components.queries_manager import ZSources
from road_eval_dashboard.pages.rem_page.utils import REM_FILTERS, REM_TYPE, get_base_graph_layout, get_rem_fig

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


layout = html.Div(
    [
        get_settings_layout(),
    ]
    + [
        get_base_graph_layout(filter_name, TAB, sort_by_dist=filter_props.get("sort_by_dist", False))
        for filter_name, filter_props in REM_FILTERS.items()
    ]
)


@callback(
    Output({"out": "graph", "filter": MATCH, "rem_type": REM_TYPE, "sort_by_dist": False, "tab": TAB}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(REM_ACCURACY_3D_SOURCE_DROPDOWN, "value"),
    Input(REM_ACCURACY_ERROR_THRESHOLD_SLIDER, "value"),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    State({"out": "graph", "filter": MATCH, "rem_type": REM_TYPE, "sort_by_dist": False, "tab": TAB}, "id"),
    background=True,
)
def get_none_dist_graph(meta_data_filters, source, error_threshold, nets, effective_samples, graph_id):
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
    )
    return fig


@callback(
    Output({"out": "graph", "filter": MATCH, "rem_type": REM_TYPE, "sort_by_dist": True, "tab": TAB}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(REM_ACCURACY_3D_SOURCE_DROPDOWN, "value"),
    Input(REM_ACCURACY_ERROR_THRESHOLD_SLIDER, "value"),
    Input({"out": "sort_by_dist", "filter": MATCH, "rem_type": REM_TYPE, "sort_by_dist": True, "tab": TAB}, "on"),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    State({"out": "graph", "filter": MATCH, "rem_type": REM_TYPE, "sort_by_dist": True, "tab": TAB}, "id"),
    background=True,
)
def get_dist_graph(meta_data_filters, source, error_threshold, sort_by_dist, nets, effective_samples, graph_id):
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
    )
    return fig


def get_accuracy_fig(
    meta_data_filters, nets, interesting_filters, effective_samples, filter_name, source, error_threshold
):
    label = f"rem_accuracy_{source}"
    pred = error_threshold
    title = f"Accuracy By {source} With Threshold {error_threshold}"
    fig = get_rem_fig(meta_data_filters, nets, interesting_filters, effective_samples, filter_name, title, label, pred)
    return fig
