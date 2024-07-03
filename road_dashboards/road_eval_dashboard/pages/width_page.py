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
    WIDTH_3D_SOURCE_DROPDOWN,
    WIDTH_AVERAGE_ERROR,
    WIDTH_ROLES_DROPDOWN,
)
from road_dashboards.road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_dashboards.road_eval_dashboard.components.layout_wrapper import card_wrapper
from road_dashboards.road_eval_dashboard.components.page_properties import PageProperties
from road_dashboards.road_eval_dashboard.components.queries_manager import (
    Roles,
    ZSources,
    generate_sum_bins_by_diff_cols_metric_query,
    generate_sum_bins_metric_query,
    generate_sum_success_rate_metric_by_Z_bins_query,
    generate_sum_success_rate_metric_query,
    run_query_with_nets_names_processing,
)
from road_dashboards.road_eval_dashboard.graphs.meta_data_filters_graph import draw_meta_data_filters

extra_properties = PageProperties("line-chart")
register_page(__name__, path="/width", name="Width", order=11, **extra_properties.__dict__)
Z_BINS = [0, 25, 50, 75, 100, 125, 150, 175, 200, 250, 300, 350, 999]
WIDTH_TYPE = "width"
WIDTH_FILTERS = {
    "road_type": {"filters": ROAD_TYPE_FILTERS},
    "lane_mark_type": {"filters": LANE_MARK_TYPE_FILTERS},
    "event": {"filters": EVENT_FILTERS},
    "weather": {"filters": WEATHER_FILTERS},
    "curve": {"filters": CURVE_BY_RAD_FILTERS, "dist_filters": CURVE_BY_DIST_FILTERS, "sort_by_dist": True},
}


def get_settings_layout():
    sources_options = [s.value for s in ZSources]
    roles_options = {s.value: s.name.capitalize() for s in Roles}
    return card_wrapper(
        [
            html.H6("Choose Role"),
            dcc.Dropdown(roles_options, Roles.HOST, id=WIDTH_ROLES_DROPDOWN),
            html.H6("Choose 3d source", style={"margin-top": 10}),
            dcc.Dropdown(sources_options, ZSources.FUSION, id=WIDTH_3D_SOURCE_DROPDOWN),
        ]
    )


def get_base_graph_layout(filter_name, sort_by_dist=False):
    layout = card_wrapper(
        [
            dbc.Row(
                graph_wrapper(
                    {
                        "out": "graph",
                        "filter": filter_name,
                        "width_type": WIDTH_TYPE,
                        "sort_by_dist": sort_by_dist,
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
                                "width_type": WIDTH_TYPE,
                                "sort_by_dist": sort_by_dist,
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


def get_width_by_Z_layout():
    return card_wrapper(
        [
            dbc.Row(
                graph_wrapper(
                    {
                        "out": "graph_by_Z",
                        "width_type": WIDTH_TYPE,
                    }
                )
            )
        ]
    )


def get_average_error_layout():
    return card_wrapper(
        [
            dbc.Row(
                graph_wrapper(
                    {"width_type": WIDTH_TYPE, "out": WIDTH_AVERAGE_ERROR},
                )
            ),
        ]
    )


layout = html.Div(
    [
        html.H1("Width Metrics", className="mb-5"),
        meta_data_filter.layout,
        base_dataset_statistics.frame_layout,
        get_settings_layout(),
        html.Div(
            [get_average_error_layout(), get_width_by_Z_layout()]
            + [
                get_base_graph_layout(filter_name, sort_by_dist=filter_props.get("sort_by_dist", False))
                for filter_name, filter_props in WIDTH_FILTERS.items()
            ]
        ),
    ]
)


@callback(
    Output({"width_type": WIDTH_TYPE, "out": WIDTH_AVERAGE_ERROR}, "figure"),
    Input(WIDTH_ROLES_DROPDOWN, "value"),
    Input(WIDTH_3D_SOURCE_DROPDOWN, "value"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
)
def get_average_error_graph(role, source, meta_data_filters, nets, effective_samples):
    labels_to_preds = get_labels_to_preds_with_names(source, pred_type="sum_error")
    query = generate_sum_bins_by_diff_cols_metric_query(
        nets["gt_tables"],
        nets["meta_data"],
        labels_to_preds=labels_to_preds,
        meta_data_filters=meta_data_filters,
        role=role,
    )
    data, _ = run_query_with_nets_names_processing(query)
    data = data.sort_values(by="net_id")
    for bin in Z_BINS[:-1]:
        data[f"score_{bin}"] = data[f"score_{bin}"] / data[f"count_{bin}"]
    fig = draw_meta_data_filters(
        data,
        list(labels_to_preds.keys()),
        get_width_score,
        effective_samples=effective_samples,
        title=f"Average Error By {source}",
        xaxis="Z Bins",
        yaxis="Avg Error",
        hover=True,
        count_items_name="points",
    )
    return fig


@callback(
    Output({"out": "graph", "filter": MATCH, "width_type": WIDTH_TYPE, "sort_by_dist": False}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(WIDTH_ROLES_DROPDOWN, "value"),
    Input(WIDTH_3D_SOURCE_DROPDOWN, "value"),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    State({"out": "graph", "filter": MATCH, "width_type": WIDTH_TYPE, "sort_by_dist": False}, "id"),
)
def get_none_dist_graph(meta_data_filters, role, source, nets, effective_samples, graph_id):
    if not nets:
        return no_update
    filter_name = graph_id["filter"]
    filters = WIDTH_FILTERS[filter_name]
    interesting_filters = filters["filters"]
    labels, preds = get_labels_and_preds(source)
    title = f"Success Rate By Role {role.capitalize()}"
    fig = get_width_fig(
        meta_data_filters,
        nets,
        interesting_filters,
        effective_samples,
        filter_name,
        title,
        filter_name,
        "Success Rate",
        labels,
        preds,
        role=role,
    )
    return fig


@callback(
    Output({"out": "graph", "filter": MATCH, "width_type": WIDTH_TYPE, "sort_by_dist": True}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(WIDTH_ROLES_DROPDOWN, "value"),
    Input(WIDTH_3D_SOURCE_DROPDOWN, "value"),
    Input({"out": "sort_by_dist", "filter": MATCH, "width_type": WIDTH_TYPE, "sort_by_dist": True}, "on"),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    State({"out": "graph", "filter": MATCH, "width_type": WIDTH_TYPE, "sort_by_dist": True}, "id"),
)
def get_dist_graph(meta_data_filters, role, source, sort_by_dist, nets, effective_samples, graph_id):
    if not nets:
        return no_update
    filter_name = graph_id["filter"]
    filters = WIDTH_FILTERS[filter_name]
    interesting_filters = filters["dist_filters"] if sort_by_dist else filters["filters"]
    labels, preds = get_labels_and_preds(source)
    title = f"Success Rate By Role {role.capitalize()}"
    fig = get_width_fig(
        meta_data_filters,
        nets,
        interesting_filters,
        effective_samples,
        filter_name,
        title,
        filter_name,
        "Success Rate",
        labels,
        preds,
        role=role,
    )
    return fig


@callback(
    Output({"out": "graph_by_Z", "width_type": WIDTH_TYPE}, "figure"),
    Input(MD_FILTERS, "data"),
    Input(WIDTH_ROLES_DROPDOWN, "value"),
    Input(WIDTH_3D_SOURCE_DROPDOWN, "value"),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
)
def get_Z_graph(meta_data_filters, role, source, nets, effective_samples):
    if not nets:
        return no_update
    labels_to_preds = get_labels_to_preds_with_names(source)
    title = f"Success Rate By Z With Role {role.capitalize()}"
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
        get_width_score,
        effective_samples=effective_samples,
        title=title,
        xaxis="Z Bins",
        yaxis="Success Rate",
        hover=True,
        count_items_name="num of gt points",
    )
    return fig


def get_labels_and_preds(source):
    base_label_name = "lm_width_gt_valid_count"
    base_pred_name = f"lm_width_{source}_success_rate"
    labels = []
    preds = []
    for i, Z in enumerate(Z_BINS[:-1]):
        next_Z = Z_BINS[i + 1]
        labels.append(f"{base_label_name}_{Z}_{next_Z}")
        preds.append(f"{base_pred_name}_{Z}_{next_Z}")
    return labels, preds


def get_labels_to_preds_with_names(source, pred_type="success_rate"):
    base_label_name = "lm_width_gt_valid_count"
    base_pred_name = f"lm_width_{source}_{pred_type}"
    labels_to_pred = {}
    for i, Z in enumerate(Z_BINS[:-1]):
        next_Z = Z_BINS[i + 1]
        labels_to_pred[f"{Z}"] = (f"{base_label_name}_{Z}_{next_Z}", f"{base_pred_name}_{Z}_{next_Z}")
    return labels_to_pred


def get_width_fig(
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
        extra_filters=" AND ".join([f"{label} >= 0" for label in labels]),
        extra_columns=labels + preds,
        role=role,
    )
    data, _ = run_query_with_nets_names_processing(query)
    filter_name_to_display = filter_name.replace("_", " ").capitalize()
    data = data.sort_values(by="net_id")
    fig = draw_meta_data_filters(
        data,
        list(interesting_filters.keys()),
        get_width_score,
        effective_samples=effective_samples,
        title=f"{title} Per {filter_name_to_display}",
        yaxis=yaxis,
        xaxis=xaxis,
        hover=True,
    )
    return fig


def get_width_score(row, filter):
    score = row[f"score_{filter}"]
    return score
