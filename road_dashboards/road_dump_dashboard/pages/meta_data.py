from dash import register_page

from road_dashboards.road_dump_dashboard.logical_components.constants.page_properties import PageProperties
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.conf_mat_graph import ConfMatGraph
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.conf_mat_with_dropdown import (
    ConfMatGraphWithDropdown,
)
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.count_graph import CountGraph
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.count_graph_with_dropdown import (
    CountGraphWithDropdown,
)
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.countries_heatmap import CountriesHeatMap
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.data_filters import DataFilters
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.dataset_selector import DatasetSelector
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.filters_aggregator import FiltersAggregator
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.frames_modal import FramesModal
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.jump_modal import JumpModal
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.objs_count_card import ObjCountCard
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.population_card import PopulationCard
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.two_datasets_selector import (
    TwoDatasetsSelector,
)
from road_dashboards.road_dump_dashboard.logical_components.multi_page_objects.grid_generator import GridGenerator
from road_dashboards.road_dump_dashboard.table_schemes.meta_data import MetaData

page = PageProperties(order=1, icon="search", path="/meta_data", title="Meta Data", main_table="meta_data")
register_page(__name__, **page.__dict__)

data_filters = DataFilters(main_table=page.main_table)
population_card = PopulationCard()
filters_agg = FiltersAggregator(population_card.final_filter_id, data_filters.final_filter_id)

obj_count_card = ObjCountCard(
    main_table=page.main_table,
    objs_name="Frames",
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
)
tv_prefects_count = CountGraph(
    column=MetaData.is_tv_perfect,
    title="Top View Perfects Exists",
    main_table=page.main_table,
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
)
gtem_count = CountGraph(
    column=MetaData.gtem_labels_exist,
    title="Gtem Exists",
    main_table=page.main_table,
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
)
curve_rad_hist = CountGraph(
    column=MetaData.curve_rad_ahead,
    title="Curve Rad Distribution",
    main_table=page.main_table,
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
    slider_value=-2,
    filter=MetaData.curve_rad_ahead != 99999,
    full_grid_row=True,
)
batches_hist = CountGraph(
    column=MetaData.batch_num,
    title="Batches Distribution",
    main_table=page.main_table,
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
    full_grid_row=True,
)
road_type_hist = CountGraph(
    column=MetaData.road_type,
    title="Road Type Distribution",
    main_table=page.main_table,
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
)
lm_color_hist = CountGraph(
    column=MetaData.lm_color,
    title="Lane Mark Color Distribution",
    main_table=page.main_table,
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
)
wildcard_count = CountGraphWithDropdown(
    main_table=page.main_table,
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
)

obj_to_hide_id = "meta_data_conf_mats"
two_datasets_selector = TwoDatasetsSelector(main_table=page.main_table, obj_to_hide_ids=[obj_to_hide_id])
tv_perfects_conf = ConfMatGraph(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    page_filters_id=filters_agg.final_filter_id,
    title="Top View Perfects Classification",
    main_table=page.main_table,
    column=MetaData.is_tv_perfect,
)
gtem_conf = ConfMatGraph(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    page_filters_id=filters_agg.final_filter_id,
    title="Gtem Classification",
    main_table=page.main_table,
    column=MetaData.gtem_labels_exist,
)
road_type_conf = ConfMatGraph(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    page_filters_id=filters_agg.final_filter_id,
    title="Road Type Classification",
    main_table=page.main_table,
    column=MetaData.road_type,
)
lm_color_conf = ConfMatGraph(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    page_filters_id=filters_agg.final_filter_id,
    title="Lane Marks Color Classification",
    main_table=page.main_table,
    column=MetaData.lm_color,
)
wildcard_conf = ConfMatGraphWithDropdown(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    page_filters_id=filters_agg.final_filter_id,
    main_table=page.main_table,
)
frames_modal = FramesModal(
    page_filters_id=filters_agg.final_filter_id,
    triggering_conf_mats=[tv_perfects_conf, gtem_conf, road_type_conf, lm_color_conf],
    triggering_dropdown_conf_mats=[wildcard_conf],
    triggering_filters=[data_filters],
)
jump_modal = JumpModal(
    page_filters_id=filters_agg.final_filter_id,
    triggering_conf_mats=[tv_perfects_conf, gtem_conf, road_type_conf, lm_color_conf],
    triggering_dropdown_conf_mats=[wildcard_conf],
    triggering_filters=[data_filters],
)

countries_dataset_selector = DatasetSelector(main_table=page.main_table)
countries_heatmap = CountriesHeatMap(
    main_table=page.main_table,
    page_filters_id=filters_agg.final_filter_id,
    datasets_dropdown_id=countries_dataset_selector.main_dataset_dropdown_id,
)


layout = GridGenerator(
    frames_modal,
    jump_modal,
    data_filters,
    obj_count_card,
    population_card,
    filters_agg,
    tv_prefects_count,
    gtem_count,
    curve_rad_hist,
    batches_hist,
    road_type_hist,
    lm_color_hist,
    wildcard_count,
    GridGenerator(
        two_datasets_selector,
        tv_perfects_conf,
        gtem_conf,
        road_type_conf,
        lm_color_conf,
        wildcard_conf,
        component_id=obj_to_hide_id,
    ),
    GridGenerator(countries_dataset_selector, countries_heatmap),
    warp_sub_objects=False,
).layout()
