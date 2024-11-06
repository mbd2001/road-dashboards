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
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.data_filters import DataFilters
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.filters_aggregator import FiltersAggregator
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.frames_modal import FramesModal
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.obj_count_graph import ObjCountGraph
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.objs_count_card import ObjCountCard
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.population_card import PopulationCard
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.two_datasets_selector import (
    TwoDatasetsSelector,
)
from road_dashboards.road_dump_dashboard.logical_components.multi_page_objects.grid_generator import GridGenerator
from road_dashboards.road_dump_dashboard.table_schemes.pathnet import PathNet

page = PageProperties(order=3, icon="search", path="/pathnet", title="Pathnet", main_table="rpw_meta_data")
register_page(__name__, **page.__dict__)

data_filters = DataFilters(main_table=page.main_table)
population_card = PopulationCard()
filters_agg = FiltersAggregator(population_card.final_filter_id, data_filters.final_filter_id)
obj_count_card = ObjCountCard(
    main_table=page.main_table,
    objs_name="DPs",
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
)
role_count = CountGraph(
    column=PathNet.dp_role,
    title="Role Distribution",
    main_table=page.main_table,
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
)
split_count = CountGraph(
    column=PathNet.dp_split_role,
    title="Split Role Distribution",
    main_table=page.main_table,
    filter=PathNet.dp_split_role != "IGNORE",
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
)
primary_count = CountGraph(
    column=PathNet.dp_primary_role,
    title="Primary Role Distribution",
    main_table=page.main_table,
    filter=PathNet.dp_primary_role != "IGNORE",
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
)
merge_count = CountGraph(
    column=PathNet.dp_merge_role,
    title="Merge Role Distribution",
    main_table=page.main_table,
    filter=PathNet.dp_merge_role != "IGNORE",
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
)
oncoming_count = CountGraph(
    column=PathNet.dp_points_oncoming,
    title="Oncoming Distribution",
    main_table=page.main_table,
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
)
obj_count = ObjCountGraph(
    main_table=page.main_table,
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
)
wildcard_count = CountGraphWithDropdown(
    main_table=page.main_table,
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
)

obj_to_hide_id = "path_net_conf_mats"
two_datasets_selector = TwoDatasetsSelector(main_table=page.main_table, obj_to_hide_id=obj_to_hide_id)
role_conf = ConfMatGraph(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    page_filters_id=filters_agg.final_filter_id,
    title="Role Classification",
    main_table=page.main_table,
    column=PathNet.dp_role,
    full_grid_row=True,
)
split_conf = ConfMatGraph(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    page_filters_id=filters_agg.final_filter_id,
    title="Split Role Classification",
    main_table=page.main_table,
    column=PathNet.dp_split_role,
    filter=PathNet.dp_split_role != "IGNORE",
)
primary_conf = ConfMatGraph(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    page_filters_id=filters_agg.final_filter_id,
    title="Primary Role Classification",
    main_table=page.main_table,
    column=PathNet.dp_primary_role,
    filter=PathNet.dp_primary_role != "IGNORE",
)
merge_conf = ConfMatGraph(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    page_filters_id=filters_agg.final_filter_id,
    title="Merge Role Classification",
    main_table=page.main_table,
    column=PathNet.dp_merge_role,
    filter=PathNet.dp_merge_role != "IGNORE",
    full_grid_row=True,
)
oncoming_conf = ConfMatGraph(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    page_filters_id=filters_agg.final_filter_id,
    title="Oncoming Classification",
    main_table=page.main_table,
    column=PathNet.dp_points_oncoming,
)
wildcard_conf = ConfMatGraphWithDropdown(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    page_filters_id=filters_agg.final_filter_id,
    main_table=page.main_table,
)
frames_modal = FramesModal(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    page_filters_id=filters_agg.final_filter_id,
    main_table=page.main_table,
    triggering_conf_mats=[role_conf, split_conf, primary_conf, merge_conf, oncoming_conf],
    triggering_dropdown_conf_mats=[wildcard_conf],
)

layout = GridGenerator(
    data_filters,
    obj_count_card,
    population_card,
    filters_agg,
    role_count,
    split_count,
    primary_count,
    merge_count,
    obj_count,
    wildcard_count,
    GridGenerator(
        two_datasets_selector,
        role_conf,
        split_conf,
        primary_conf,
        merge_conf,
        wildcard_conf,
        frames_modal,
        component_id=obj_to_hide_id,
    ),
    warp_sub_objects=False,
).layout()
