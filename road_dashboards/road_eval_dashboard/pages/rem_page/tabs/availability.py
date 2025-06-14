from dash import MATCH, Input, Output, State, callback, html, no_update

from road_dashboards.road_eval_dashboard.components.components_ids import (
    EFFECTIVE_SAMPLES_PER_BATCH,
    MD_FILTERS,
    NETS,
    REM_ROLES_DROPDOWN,
    REM_SOURCE_DROPDOWN,
)
from road_dashboards.road_eval_dashboard.pages.rem_page.utils import (
    REM_FILTERS,
    REM_TYPE,
    get_base_graph_layout,
    get_rem_fig,
)

TAB = "availability"

layout = html.Div(
    [
        get_base_graph_layout(filter_name, TAB, sort_by_dist=filter_props.get("sort_by_dist", False))
        for filter_name, filter_props in REM_FILTERS.items()
    ]
)


@callback(
    Output(
        {
            "out": "graph",
            "filter": MATCH,
            "rem_type": REM_TYPE,
            "sort_by_dist": False,
            "tab": TAB,
            "tab_type": "regular",
        },
        "figure",
    ),
    Input(MD_FILTERS, "data"),
    Input(REM_ROLES_DROPDOWN, "value"),
    Input({"rem_type": REM_TYPE, "out": REM_SOURCE_DROPDOWN}, "value"),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    State(
        {
            "out": "graph",
            "filter": MATCH,
            "rem_type": REM_TYPE,
            "sort_by_dist": False,
            "tab": TAB,
            "tab_type": "regular",
        },
        "id",
    ),
)
def get_none_dist_graph(meta_data_filters, role, Z_source, nets, effective_samples, graph_id):
    if not nets:
        return no_update
    filter_name = graph_id["filter"]
    filters = REM_FILTERS[filter_name]
    interesting_filters = filters["filters"]
    fig = get_availability_fig(
        meta_data_filters=meta_data_filters,
        nets=nets,
        interesting_filters=interesting_filters,
        effective_samples=effective_samples,
        filter_name=filter_name,
        role=role,
        Z_source=Z_source,
    )
    return fig


@callback(
    Output(
        {
            "out": "graph",
            "filter": MATCH,
            "rem_type": REM_TYPE,
            "sort_by_dist": True,
            "tab": TAB,
            "tab_type": "regular",
        },
        "figure",
    ),
    Input(MD_FILTERS, "data"),
    Input(REM_ROLES_DROPDOWN, "value"),
    Input({"rem_type": REM_TYPE, "out": REM_SOURCE_DROPDOWN}, "value"),
    Input(
        {
            "out": "sort_by_dist",
            "filter": MATCH,
            "rem_type": REM_TYPE,
            "sort_by_dist": True,
            "tab": TAB,
            "tab_type": "regular",
        },
        "on",
    ),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    State(
        {
            "out": "graph",
            "filter": MATCH,
            "rem_type": REM_TYPE,
            "sort_by_dist": True,
            "tab": TAB,
            "tab_type": "regular",
        },
        "id",
    ),
)
def get_dist_graph(meta_data_filters, role, Z_source, sort_by_dist, nets, effective_samples, graph_id):
    if not nets:
        return no_update
    filter_name = graph_id["filter"]
    filters = REM_FILTERS[filter_name]
    interesting_filters = filters["dist_filters"] if sort_by_dist else filters["filters"]
    fig = get_availability_fig(
        meta_data_filters=meta_data_filters,
        nets=nets,
        interesting_filters=interesting_filters,
        effective_samples=effective_samples,
        filter_name=filter_name,
        role=role,
        Z_source=Z_source,
    )
    return fig


def get_availability_fig(
    meta_data_filters, nets, interesting_filters, effective_samples, filter_name, Z_source, role=""
):
    label = f"rem_availability_{Z_source}"
    pred = 1
    title = "Availability"
    fig = get_rem_fig(
        meta_data_filters,
        nets,
        interesting_filters,
        effective_samples,
        filter_name,
        title,
        filter_name,
        "Success Rate",
        label,
        pred,
        compare_operator="=",
        role=role,
    )
    return fig
