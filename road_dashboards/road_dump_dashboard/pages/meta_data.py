from dash import html, register_page

from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import META_DATA
from road_dashboards.road_dump_dashboard.logical_components.constants.page_properties import PageProperties
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.columns_dropdown import ColumnsDropdown
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.conf_mat_graph import ConfMatGraph
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.count_graph import CountGraph
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.countries_heatmap import CountriesHeatMap
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.data_filters import DataFilters
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.dataset_selector import DatasetSelector
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.filters_aggregator import FiltersAggregator
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.frames_modal import FramesModal
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.jump_modal import JumpModal
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.objs_count_card import ObjCountCard
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.population_card import PopulationCard
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.switch import Switch
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.two_datasets_selector import (
    TwoDatasetsSelector,
)
from road_dashboards.road_dump_dashboard.logical_components.multi_page_objects.grid_generator import GridGenerator
from road_dashboards.road_dump_dashboard.table_schemes.meta_data import MetaData

page = PageProperties(order=2, icon="search", path="/meta_data", title="Meta Data", main_table=META_DATA)
register_page(__name__, **page.__dict__)

data_filters = DataFilters(main_table=page.main_table)
population_card = PopulationCard()
intersection_switch = Switch("Intersection")
filters_agg = FiltersAggregator(population_card.final_filter_id, data_filters.final_filter_id)

obj_count_card = ObjCountCard(
    main_table=page.main_table,
    objs_name="Frames",
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=intersection_switch.component_id,
)
tv_prefects_count = CountGraph(
    main_table=page.main_table,
    title="Top View Perfects Exists",
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=intersection_switch.component_id,
    column=MetaData.is_tv_perfect,
)
gtem_count = CountGraph(
    main_table=page.main_table,
    title="Gtem Exists",
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=intersection_switch.component_id,
    column=MetaData.gtem_labels_exist,
)
curve_rad_hist = CountGraph(
    main_table=page.main_table,
    title="Curve Rad Distribution",
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=intersection_switch.component_id,
    column=MetaData.curve_rad_ahead,
    filter=MetaData.curve_rad_ahead != 99999,
    slider_value=-2,
    full_grid_row=True,
)
road_type_hist = CountGraph(
    main_table=page.main_table,
    title="Road Type Distribution",
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=intersection_switch.component_id,
    column=MetaData.road_type,
)
lm_color_hist = CountGraph(
    main_table=page.main_table,
    title="Lane Mark Color Distribution",
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=intersection_switch.component_id,
    column=MetaData.lm_color,
)
count_columns_dropdown = ColumnsDropdown(main_table=page.main_table, full_grid_row=True)
wildcard_count = CountGraph(
    main_table=count_columns_dropdown.main_table,
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=intersection_switch.component_id,
    columns_dropdown_id=count_columns_dropdown.component_id,
    slider_value=1,
    full_grid_row=True,
)

obj_to_hide_id = "meta_data_conf_mats"
two_datasets_selector = TwoDatasetsSelector(main_table=page.main_table, obj_to_hide_ids=[obj_to_hide_id])
tv_perfects_conf = ConfMatGraph(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    main_table=two_datasets_selector.main_table,
    page_filters_id=filters_agg.final_filter_id,
    title="Top View Perfects Classification",
    column=MetaData.is_tv_perfect,
)
gtem_conf = ConfMatGraph(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    main_table=two_datasets_selector.main_table,
    page_filters_id=filters_agg.final_filter_id,
    title="Gtem Classification",
    column=MetaData.gtem_labels_exist,
)
road_type_conf = ConfMatGraph(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    main_table=two_datasets_selector.main_table,
    page_filters_id=filters_agg.final_filter_id,
    title="Road Type Classification",
    column=MetaData.road_type,
)
lm_color_conf = ConfMatGraph(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    main_table=two_datasets_selector.main_table,
    page_filters_id=filters_agg.final_filter_id,
    title="Lane Marks Color Classification",
    column=MetaData.lm_color,
)
conf_columns_dropdown = ColumnsDropdown(main_table=two_datasets_selector.main_table, full_grid_row=True)
wildcard_conf = ConfMatGraph(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    main_table=two_datasets_selector.main_table,
    page_filters_id=filters_agg.final_filter_id,
    columns_dropdown_id=conf_columns_dropdown.component_id,
)

frames_modal = FramesModal(
    page_filters_id=filters_agg.final_filter_id,
    triggering_conf_mats=[tv_perfects_conf, gtem_conf, road_type_conf, lm_color_conf, wildcard_conf],
    triggering_filters=[data_filters],
)
jump_modal = JumpModal(
    page_filters_id=filters_agg.final_filter_id,
    triggering_conf_mats=[tv_perfects_conf, gtem_conf, road_type_conf, lm_color_conf, wildcard_conf],
    triggering_filters=[data_filters],
)

countries_dataset_selector = DatasetSelector(main_table=page.main_table)
countries_heatmap = CountriesHeatMap(
    main_table=conf_columns_dropdown.main_table,
    datasets_dropdown_id=countries_dataset_selector.main_dataset_dropdown_id,
    page_filters_id=filters_agg.final_filter_id,
)

layout = GridGenerator(
    frames_modal,
    jump_modal,
    data_filters,
    obj_count_card,
    GridGenerator(html.H3("Population"), population_card, intersection_switch, full_grid_row=False),
    filters_agg,
    tv_prefects_count,
    gtem_count,
    curve_rad_hist,
    road_type_hist,
    lm_color_hist,
    GridGenerator(
        count_columns_dropdown,
        wildcard_count,
    ),
    GridGenerator(
        two_datasets_selector,
        tv_perfects_conf,
        gtem_conf,
        road_type_conf,
        lm_color_conf,
        GridGenerator(conf_columns_dropdown, wildcard_conf),
        component_id=obj_to_hide_id,
    ),
    GridGenerator(countries_dataset_selector, countries_heatmap),
    warp_sub_objects=False,
).layout()
