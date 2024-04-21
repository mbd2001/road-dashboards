
from dash import html, callback, Output, Input, State, MATCH, no_update

from road_eval_dashboard.components.components_ids import MD_FILTERS, NETS, EFFECTIVE_SAMPLES_PER_BATCH
from road_eval_dashboard.pages.rem_page.utils import get_base_graph_layout, REM_FILTERS, REM_TYPE, get_rem_fig

TAB = "painted"

layout = html.Div([
        get_base_graph_layout(filter_name, TAB, sort_by_dist=filter_props.get("sort_by_dist", False))
        for filter_name, filter_props in REM_FILTERS.items()]
)

@callback(
    Output({"out": "graph", "filter": MATCH, "rem_type": REM_TYPE, "sort_by_dist": False, "tab": TAB}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    State({"out": "graph", "filter": MATCH, "rem_type": REM_TYPE, "sort_by_dist": False, "tab": TAB}, "id"),
    background=True,
)
def get_none_dist_graph(meta_data_filters, nets, effective_samples, graph_id):
    if not nets:
        return no_update
    filter_name = graph_id["filter"]
    filters = REM_FILTERS[filter_name]
    interesting_filters = filters["filters"]
    fig = get_painted_fig(
        meta_data_filters=meta_data_filters,
        nets=nets,
        interesting_filters=interesting_filters,
        effective_samples=effective_samples,
        filter_name=filter_name,
    )
    return fig


@callback(
    Output({"out": "graph", "filter": MATCH, "rem_type": REM_TYPE, "sort_by_dist": True, "tab": TAB}, "figure"),
    Input(MD_FILTERS, "data"),
    Input({"out": "sort_by_dist", "filter": MATCH, "rem_type": REM_TYPE, "sort_by_dist": True, "tab": TAB}, "on"),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    State({"out": "graph", "filter": MATCH, "rem_type": REM_TYPE, "sort_by_dist": True, "tab": TAB}, "id"),
    background=True,
)
def get_dist_graph(meta_data_filters, sort_by_dist, nets, effective_samples, graph_id):
    if not nets:
        return no_update
    filter_name = graph_id["filter"]
    filters = REM_FILTERS[filter_name]
    interesting_filters = filters["dist_filters"] if sort_by_dist else filters["filters"]
    fig = get_painted_fig(
        meta_data_filters=meta_data_filters,
        nets=nets,
        interesting_filters=interesting_filters,
        effective_samples=effective_samples,
        filter_name=filter_name,
    )
    return fig

def get_painted_fig(
    meta_data_filters,
    nets,
    interesting_filters,
    effective_samples,
    filter_name,
):
    label = "rem_point_index"
    pred = "rem_painted_pred_point"
    title = f"Painted"
    fig = get_rem_fig(meta_data_filters,
    nets,
    interesting_filters,
    effective_samples,
    filter_name, title, label, pred, compare_operator="=")
    return fig