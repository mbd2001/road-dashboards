from dash import MATCH, Input, Output, State, callback, html, no_update

from road_dashboards.road_eval_dashboard.components.components_ids import (
    EFFECTIVE_SAMPLES_PER_BATCH,
    MD_FILTERS,
    NETS,
    REM_ROLES_DROPDOWN,
    REM_SOURCE_DROPDOWN,
)
from road_dashboards.road_eval_dashboard.components.queries_manager import (
    DYNAMIC_METRICS_QUERY,
    generate_base_data,
    generate_intersect_filter,
    run_query_with_nets_names_processing,
)
from road_dashboards.road_eval_dashboard.graphs.meta_data_filters_graph import draw_meta_data_filters
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
def get_none_dist_graph(meta_data_filters, role, source, nets, effective_samples, graph_id):
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
        source=source,
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
def get_dist_graph(meta_data_filters, role, source, sort_by_dist, nets, effective_samples, graph_id):
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
        source=source,
        role=role,
    )
    return fig


def get_falses_query(
    data_tables,
    meta_data,
    interesting_filters,
    Z_source,
    meta_data_filters="",
    extra_columns=[],
    role="",
):
    BASE_QUERY = """
        SELECT * FROM 
        (SELECT clip_name, grabIndex, net_id, match, COUNT(*) as group_size, MIN(rem_{Z_source}_point_sec) as rem_point_sec, MIN(rem_{Z_source}_point_Z) as rem_point_z FROM (SELECT * FROM
        ({base_data})
        {intersect_filter})
        WHERE ignore=False AND confidence > 0 AND role='{role}' AND rem_{Z_source}_point_index >= 0 
        group by net_id, clip_name, grabIndex, match) 
        INNER JOIN ({meta_data}) USING (clip_name, grabIndex)
        WHERE TRUE {meta_data_filters}
        """

    FALSE_GT_METRIC = """
    SUM(CASE WHEN match <> -1 {extra_filters} THEN group_size - 1 ELSE 0 END) as "score_gt_{ind}"
    """
    FALSE_NONE_GT_METRIC = """
        SUM(CASE WHEN match = -1 {extra_filters} THEN group_size ELSE 0 END) as "score_none_gt_{ind}"
        """
    COUNT_METRIC = """
    SUM(CASE WHEN TRUE {extra_filters} THEN group_size ELSE 0 END) as "count_{ind}"
"""
    metrics_list = []
    for metric in [COUNT_METRIC, FALSE_GT_METRIC, FALSE_NONE_GT_METRIC]:
        metrics_list += [
            metric.format(extra_filters=f"AND ({filter})", ind=name) for name, filter in interesting_filters.items()
        ]
    metrics = ", ".join(metrics_list)

    base_data = generate_base_data(data_tables["paths"], data_tables["required_columns"], extra_columns)
    intersect_filter = generate_intersect_filter(data_tables["paths"])
    base_query = BASE_QUERY.format(
        base_data=base_data,
        intersect_filter=intersect_filter,
        role=role,
        meta_data=meta_data,
        meta_data_filters=meta_data_filters,
        Z_source=Z_source,
    )
    query = DYNAMIC_METRICS_QUERY.format(metrics=metrics, base_query=base_query, group_by="net_id")
    return query


def get_falses_fig(meta_data_filters, nets, interesting_filters, effective_samples, filter_name, source, role=""):
    title = f"Falses Percentage By {source}"
    query = get_falses_query(
        nets["pred_tables"],
        nets["meta_data"],
        interesting_filters,
        Z_source=source,
        meta_data_filters=meta_data_filters,
        extra_columns=[f"rem_{source}_point_sec", f"rem_{source}_point_Z", f"rem_{source}_point_index"],
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


def get_falses_score(row, filter):
    score = (
        (row[f"score_gt_{filter}"] + row[f"score_none_gt_{filter}"]) / row[f"count_{filter}"]
        if row[f"count_{filter}"] != 0
        else 0
    )
    return score
