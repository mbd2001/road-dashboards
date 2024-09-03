from typing import List

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, html, no_update, page_registry

from road_dashboards.road_dump_dashboard.components.constants.components_ids import (
    INTERSECTION_SWITCH,
    MAIN_TABLES,
    MD_TABLES,
    OBJS_COUNT,
    PAGE_FILTERS,
    URL,
)
from road_dashboards.road_dump_dashboard.components.constants.queries_properties import (
    BaseDataQuery,
    CountMetric,
    GroupByQuery,
)
from road_dashboards.road_dump_dashboard.components.dashboard_layout.layout_wrappers import (
    card_wrapper,
    loading_wrapper,
)
from road_dashboards.road_dump_dashboard.components.logical_components.tables_properties import load_object
from road_dashboards.road_eval_dashboard.components.net_properties import Table

layout = card_wrapper(loading_wrapper(dbc.Accordion(id=OBJS_COUNT, always_open=True)))


@callback(
    Output(OBJS_COUNT, "children"),
    Output(OBJS_COUNT, "active_item"),
    Input(PAGE_FILTERS, "data"),
    Input(MAIN_TABLES, "data"),
    Input(MD_TABLES, "data"),
    Input(INTERSECTION_SWITCH, "on"),
    State(URL, "pathname"),
)
def get_frame_count(page_filters, main_tables, md_tables, intersection_on, pathname):
    if not main_tables:
        return no_update, no_update

    main_tables: List[Table] = load_object(main_tables).tables
    md_tables: List[Table] = load_object(md_tables).tables if md_tables else None
    page_properties = page_registry[f"pages.{pathname.strip('/')}"]
    objs_name = page_properties["objs_name"]
    query = GroupByQuery(
        group_by_columns=[],
        sub_query=BaseDataQuery(
            main_tables=main_tables,
            meta_data_tables=md_tables,
            page_filters=page_filters,
            intersection_on=intersection_on,
        ),
        metric=CountMetric(format_number=True),
    )
    data = query.get_results()
    frame_count_accordion = [
        dbc.AccordionItem(
            html.H5(f"{amount} {objs_name.title()}"),
            title=dump_name.title(),
            item_id=dump_name,
        )
        for dump_name, amount in zip(data.dump_name, data.overall)
    ]
    return frame_count_accordion, list(data.dump_name)
