import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import ALL, MATCH, Input, Output, State, callback, dcc, html, no_update, register_page

from road_dashboards.road_eval_dashboard.components import base_dataset_statistics, meta_data_filter
from road_dashboards.road_eval_dashboard.components.common_filters import (
    CURVE_BY_DIST_FILTERS,
    CURVE_BY_RAD_FILTERS,
    EVENT_FILTERS,
    LANE_MARK_TYPE_FILTERS,
    ROAD_TYPE_FILTERS,
    WEATHER_FILTERS,
)
from road_dashboards.road_eval_dashboard.components.components_ids import (
    EFFECTIVE_SAMPLES_PER_BATCH,
    MD_FILTERS,
    NETS,
    PAINTED_ROLES_DROPDOWN,
    PAINTED_TABS,
    PAINTED_TABS_CONTENT,
)
from road_dashboards.road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_dashboards.road_eval_dashboard.components.layout_wrapper import card_wrapper
from road_dashboards.road_eval_dashboard.components.page_properties import PageProperties
from road_dashboards.road_eval_dashboard.components.queries_manager import (
    Roles,
    generate_sum_success_rate_metric_by_Z_bins_query,
    generate_sum_success_rate_metric_query,
    run_query_with_nets_names_processing,
)
from road_dashboards.road_eval_dashboard.graphs.meta_data_filters_graph import draw_meta_data_filters

extra_properties = PageProperties("line-chart")
register_page(__name__, path="/painted", name="Painted", order=10, **extra_properties.__dict__)
Z_BINS = [0, 25, 50, 75, 100, 125, 150, 175, 200, 250, 300, 350, 999]
TP_TAB = "tp"
OVERALL_TAB = "overall"
TN_TAB = "tn"
PAINTED_TYPE = "painted"
PAINTED_FILTERS = {
    "road_type": {"filters": ROAD_TYPE_FILTERS},
    "lane_mark_type": {"filters": LANE_MARK_TYPE_FILTERS},
    "event": {"filters": EVENT_FILTERS},
    "weather": {"filters": WEATHER_FILTERS},
    "curve": {"filters": CURVE_BY_RAD_FILTERS, "dist_filters": CURVE_BY_DIST_FILTERS, "sort_by_dist": True},
}


def get_settings_layout():
    roles_options = {s.value: s.name.capitalize() for s in Roles}
    return card_wrapper(
        [
            html.H6("Choose Role"),
            dcc.Dropdown(roles_options, Roles.HOST, id=PAINTED_ROLES_DROPDOWN),
        ]
    )


def get_base_graph_layout(filter_name, tab, sort_by_dist=False):
    layout = card_wrapper(
        [
            dbc.Row(
                graph_wrapper(
                    {
                        "out": "graph",
                        "filter": filter_name,
                        "painted_type": PAINTED_TYPE,
                        "sort_by_dist": sort_by_dist,
                        "tab": tab,
                    }
                )
            ),
            dbc.Stack(
                (
                    [
                        daq.BooleanSwitch(
                            id={
                                "out": "sort_by_dist",
                                "filter": filter_name,
                                "painted_type": PAINTED_TYPE,
                                "sort_by_dist": sort_by_dist,
                                "tab": tab,
                            },
                            on=False,
                            label="Sort By Dist",
                            labelPosition="top",
                            persistence=True,
                            persistence_type="session",
                        )
                    ]
                    if sort_by_dist
                    else []
                ),
                direction="horizontal",
                gap=3,
            ),
        ]
    )
    return layout


def get_painted_by_Z_layout(tab):
    return card_wrapper(
        [
            dbc.Row(
                graph_wrapper(
                    {
                        "out": "graph_by_Z",
                        "painted_type": PAINTED_TYPE,
                        "tab": tab,
                    }
                )
            )
        ]
    )


layout = html.Div(
    [
        html.H1("Painted Metrics", className="mb-5"),
        meta_data_filter.layout,
        base_dataset_statistics.frame_layout,
        get_settings_layout(),
        dcc.Tabs(
            id=PAINTED_TABS,
            value=OVERALL_TAB,
            children=[
                dcc.Tab(label="Overall", value=OVERALL_TAB),
                dcc.Tab(label="TP Rate", value=TP_TAB),
                dcc.Tab(label="TN Rate", value=TN_TAB),
            ],
            style={"margin-top": 15},
        ),
        html.Div(id=PAINTED_TABS_CONTENT),
    ]
)


def get_tab_layout(tab):
    filter_graphs = [
        get_base_graph_layout(filter_name, tab, sort_by_dist=filter_props.get("sort_by_dist", False))
        for filter_name, filter_props in PAINTED_FILTERS.items()
    ]
    return html.Div([get_painted_by_Z_layout(tab)] + filter_graphs)


@callback(Output(PAINTED_TABS_CONTENT, "children"), Input(PAINTED_TABS, "value"))
def render_content(tab):
    return get_tab_layout(tab)


@callback(
    Output(
        {"out": "graph", "filter": MATCH, "painted_type": PAINTED_TYPE, "sort_by_dist": False, "tab": ALL}, "figure"
    ),
    Input(MD_FILTERS, "data"),
    Input(PAINTED_ROLES_DROPDOWN, "value"),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    State({"out": "graph", "filter": MATCH, "painted_type": PAINTED_TYPE, "sort_by_dist": False, "tab": ALL}, "id"),
)
def get_none_dist_graph(meta_data_filters, role, nets, effective_samples, graph_id):
    if not nets:
        return no_update
    graph_id = graph_id[0]
    tab = graph_id["tab"]
    filter_name = graph_id["filter"]
    filters = PAINTED_FILTERS[filter_name]
    interesting_filters = filters["filters"]
    labels, preds = get_labels_and_preds_by_tab(tab)
    title = f"{tab.upper()} Rate By Role {role.capitalize()}"
    fig = get_painted_fig(
        meta_data_filters,
        nets,
        interesting_filters,
        effective_samples,
        filter_name,
        title,
        filter_name,
        f"{tab.upper()} Rate",
        labels,
        preds,
        role=role,
    )
    return [fig]


@callback(
    Output({"out": "graph", "filter": MATCH, "painted_type": PAINTED_TYPE, "sort_by_dist": True, "tab": ALL}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PAINTED_ROLES_DROPDOWN, "value"),
    Input(
        {"out": "sort_by_dist", "filter": MATCH, "painted_type": PAINTED_TYPE, "sort_by_dist": True, "tab": ALL}, "on"
    ),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    State({"out": "graph", "filter": MATCH, "painted_type": PAINTED_TYPE, "sort_by_dist": True, "tab": ALL}, "id"),
)
def get_dist_graph(meta_data_filters, role, sort_by_dist, nets, effective_samples, graph_id):
    if not nets:
        return no_update
    graph_id = graph_id[0]
    tab = graph_id["tab"]
    filter_name = graph_id["filter"]
    filters = PAINTED_FILTERS[filter_name]
    interesting_filters = filters["dist_filters"] if sort_by_dist else filters["filters"]
    labels, preds = get_labels_and_preds_by_tab(tab)
    title = f"{tab.upper()} Rate By Role {role.capitalize()}"
    fig = get_painted_fig(
        meta_data_filters,
        nets,
        interesting_filters,
        effective_samples,
        filter_name,
        title,
        filter_name,
        f"{tab.upper()} Rate",
        labels,
        preds,
        role=role,
    )
    return [fig]


@callback(
    Output({"out": "graph_by_Z", "painted_type": PAINTED_TYPE, "tab": ALL}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(PAINTED_ROLES_DROPDOWN, "value"),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    State({"out": "graph_by_Z", "painted_type": PAINTED_TYPE, "tab": ALL}, "id"),
)
def get_Z_graph(meta_data_filters, role, nets, effective_samples, graph_id):
    if not nets:
        return no_update
    graph_id = graph_id[0]
    tab = graph_id["tab"]
    labels_to_preds = get_labels_to_preds_with_names_by_tab(tab)
    title = f"{tab.upper()} Rate By Z With Role {role.capitalize()}"
    query = generate_sum_success_rate_metric_by_Z_bins_query(
        nets["gt_tables"],
        nets["meta_data"],
        labels_to_preds,
        meta_data_filters=meta_data_filters,
        role=role,
    )
    data, _ = run_query_with_nets_names_processing(query)
    data = data.sort_values(by="net_id")
    fig = draw_meta_data_filters(
        data,
        list(labels_to_preds.keys()),
        get_painted_score,
        effective_samples=effective_samples,
        title=title,
        xaxis="Z Bins",
        yaxis=f"{tab.upper()} Rate",
        hover=True,
        count_items_name="num of gt points",
    )
    return [fig]


def get_labels_and_preds_by_tab(tab):
    labels = []
    preds = []
    tabs = [tab] if tab != OVERALL_TAB else [TP_TAB, TN_TAB]
    for t in tabs:
        base_label_name = "gt_painted_count" if t == TP_TAB else "gt_not_painted_count"
        base_pred_name = "pred_true_positive" if t == TP_TAB else "pred_true_negative"
        for i, Z in enumerate(Z_BINS[:-1]):
            next_Z = Z_BINS[i + 1]
            labels.append(f"{base_label_name}_{Z}_{next_Z}")
            preds.append(f"{base_pred_name}_{Z}_{next_Z}")
    return labels, preds


def get_labels_to_preds_with_names_by_tab(tab):
    labels_to_pred = {}
    tabs = [tab] if tab != OVERALL_TAB else [TP_TAB, TN_TAB]
    for i, Z in enumerate(Z_BINS[:-1]):
        next_Z = Z_BINS[i + 1]
        label_names = []
        pred_names = []
        for t in tabs:
            base_label_name = "gt_painted_count" if t == TP_TAB else "gt_not_painted_count"
            base_pred_name = "pred_true_positive" if t == TP_TAB else "pred_true_negative"
            label_names.append(f"{base_label_name}_{Z}_{next_Z}")
            pred_names.append(f"{base_pred_name}_{Z}_{next_Z}")
        labels_to_pred[f"{Z}"] = ("+".join(label_names), "+".join(pred_names))
    return labels_to_pred


def get_painted_fig(
    meta_data_filters,
    nets,
    interesting_filters,
    effective_samples,
    filter_name,
    title,
    xaxis,
    yaxis,
    labels,
    preds,
    role="",
):
    query = generate_sum_success_rate_metric_query(
        nets["gt_tables"],
        nets["meta_data"],
        "+".join(labels),
        "+".join(preds),
        interesting_filters,
        meta_data_filters=meta_data_filters,
        extra_filters=" AND ".join([f"{label} != -1" for label in labels]),
        extra_columns=labels + preds,
        role=role,
    )
    data, _ = run_query_with_nets_names_processing(query)
    filter_name_to_display = filter_name.replace("_", " ").capitalize()
    data = data.sort_values(by="net_id")
    fig = draw_meta_data_filters(
        data,
        list(interesting_filters.keys()),
        get_painted_score,
        effective_samples=effective_samples,
        title=f"{title} Per {filter_name_to_display}",
        xaxis=xaxis,
        yaxis=yaxis,
        hover=True,
    )
    return fig


def get_painted_score(row, filter):
    score = row[f"score_{filter}"]
    return score
