from dash import MATCH, Input, Output, State, callback, html, no_update

from road_dashboards.road_eval_dashboard.components.components_ids import (
    EFFECTIVE_SAMPLES_PER_BATCH,
    MD_FILTERS,
    NETS,
    REM_ROLES_DROPDOWN,
    REM_SOURCE_DROPDOWN,
)
from road_dashboards.road_eval_dashboard.components.queries_manager import (
    run_query_with_nets_names_processing,
)
from road_dashboards.road_eval_dashboard.graphs.meta_data_filters_graph import draw_meta_data_filters
from road_dashboards.road_eval_dashboard.pages.rem_page.tabs.falses.queries import get_falses_query
from road_dashboards.road_eval_dashboard.pages.rem_page.utils import REM_FILTERS, REM_TYPE, get_base_graph_layout

TAB = "falses"

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
    fig = get_falses_fig(
        meta_data_filters=meta_data_filters,
        nets=nets,
        interesting_filters=interesting_filters,
        effective_samples=effective_samples,
        filter_name=filter_name,
        Z_source=Z_source,
        role=role,
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
    fig = get_falses_fig(
        meta_data_filters=meta_data_filters,
        nets=nets,
        interesting_filters=interesting_filters,
        effective_samples=effective_samples,
        filter_name=filter_name,
        Z_source=Z_source,
        role=role,
    )
    return fig


def get_falses_fig(meta_data_filters, nets, interesting_filters, effective_samples, filter_name, Z_source, role=""):
    title = f"Falses Percentage By {Z_source}"
    query = get_falses_query(
        nets["pred_tables"],
        nets["meta_data"],
        interesting_filters,
        Z_source=Z_source,
        meta_data_filters=meta_data_filters,
        extra_columns=[f"rem_{Z_source}_point_sec", f"rem_{Z_source}_point_Z", f"rem_{Z_source}_point_index"],
        role=role,
    )
    data, _ = run_query_with_nets_names_processing(query)
    filter_name_to_display = filter_name.replace("_", " ").capitalize()
    data = data.sort_values(by="net_id")
    fig = draw_meta_data_filters(
        data,
        list(interesting_filters.keys()),
        get_falses_score,
        effective_samples=effective_samples,
        title=f"{title} Per {filter_name_to_display}",
        xaxis=filter_name_to_display,
        yaxis="Falses Percentage",
        hover=True,
    )
    return fig


def get_falses_score(row, intresting_filter):
    score = (
        (row[f"score_gt_{intresting_filter}"] + row[f"score_none_gt_{intresting_filter}"]) / row[f"count_{intresting_filter}"]
        if row[f"count_{intresting_filter}"] != 0
        else 0
    )
    return score
