import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, html, no_update, page_registry

from road_dashboards.road_dump_dashboard.components.common_pages_layout import (
    data_filters,
    intersection_data_switch,
    objs_count_card,
    population_card,
)
from road_dashboards.road_dump_dashboard.components.constants.columns_properties import Column
from road_dashboards.road_dump_dashboard.components.constants.components_ids import (
    FILTER_ROW,
    FILTERS,
    MAIN_TABLES,
    MD_TABLES,
    PAGE_FILTERS,
    POPULATION_DROPDOWN,
    UPDATE_FILTERS_BTN,
    URL,
)
from road_dashboards.road_dump_dashboard.components.logical_components.tables_properties import POTENTIAL_TABLES


def layout(title: str) -> html.Div:
    page_header_layout = html.Div(
        [
            html.H1(title, className="mb-5"),
            data_filters.layout,
            dbc.Row(
                [
                    dbc.Col(objs_count_card.layout),
                    dbc.Col(population_card.layout),
                    dbc.Col(intersection_data_switch.layout),
                ]
            ),
        ]
    )
    return page_header_layout


@callback(
    Output(MAIN_TABLES, "data"),
    Output(MD_TABLES, "data"),
    Input(URL, "pathname"),
    [Input(table, "data") for table in POTENTIAL_TABLES],
)
def init_page_tables(pathname, *args):
    page_properties = page_registry[f"pages.{pathname.strip('/')}"]
    main_tables_name = page_properties["main_table"]
    md_tables_name = page_properties["meta_data_table"]
    if not any(args) or not main_tables_name:
        return None, None

    main_tables = args[POTENTIAL_TABLES.index(main_tables_name)]
    md_tables = args[POTENTIAL_TABLES.index(md_tables_name)] if md_tables_name else None
    return main_tables, md_tables


@callback(
    Output(PAGE_FILTERS, "data"),
    Input(UPDATE_FILTERS_BTN, "n_clicks"),
    Input(POPULATION_DROPDOWN, "value"),
    State(FILTERS, "children"),
)
def generate_curr_filters(n_clicks, population, filters):
    if not filters or not population:
        return ""

    first_group = filters[0]
    filters_str = recursive_build_meta_data_filters(first_group)
    filters_str = f"({filters_str}) " if filters_str else ""
    population_filter = f"(A.population = '{population}') " if population != "all" else ""
    filters_str = " AND ".join(ftr for ftr in [filters_str, population_filter] if ftr)
    return filters_str


def recursive_build_meta_data_filters(filters):
    # removed filter case
    if filters["props"]["style"].get("display") == "none":
        return ""

    # single filter case
    if filters["props"]["id"]["type"] == FILTER_ROW:
        row = filters["props"]
        column = row["children"][0]["props"]["children"]["props"]["value"]
        operation = row["children"][1]["props"]["children"]["props"]["value"]
        value = row["children"][2]["props"]["children"]["props"]["value"]
        single_filter = parse_one_filter(Column(column), operation, value)
        return single_filter

    # group case
    and_or_is_on = filters["props"]["children"][0]["props"]["children"][0]["props"]["on"]
    and_or_operator = " OR " if and_or_is_on else " AND "
    filters = filters["props"]["children"][1]["props"]["children"]
    sub_filters = [recursive_build_meta_data_filters(flt) for flt in filters]
    filters_str = and_or_operator.join(sub_filter for sub_filter in sub_filters if sub_filter)
    return filters_str


def parse_one_filter(column: Column, operation: str, value: str | int):
    if operation == "LIKE":
        parsed_val = f"'{value}'"
    elif operation == "IN":
        parsed_val = f"({', '.join(val for val in value)})"
    else:
        parsed_val = str(value)

    filter_components = [column.get_column_string(), operation, parsed_val]
    single_filter = " ".join(component for component in filter_components if component)
    return single_filter
