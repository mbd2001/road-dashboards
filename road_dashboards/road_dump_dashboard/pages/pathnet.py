from dash import register_page

from road_dashboards.road_dump_dashboard.logical_components.constants.page_properties import PageProperties
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.columns_dropdown import ColumnsDropdown
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.conf_mat_graph import ConfMatGraph
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.count_graph import CountGraph
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.data_filters import DataFilters
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.filters_aggregator import FiltersAggregator
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.frames_modal import FramesModal
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.jump_modal import JumpModal
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.obj_count_graph import ObjCountGraph
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.objs_count_card import ObjCountCard
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.population_card import PopulationCard
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.two_datasets_selector import (
    TwoDatasetsSelector,
)
from road_dashboards.road_dump_dashboard.logical_components.multi_page_objects.grid_generator import GridGenerator
from road_dashboards.road_dump_dashboard.table_schemes.pathnet import PathNet

page = PageProperties(order=4, icon="search", path="/pathnet", title="Pathnet", main_table="rpw_meta_data")
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
    main_table=page.main_table,
    title="Role Distribution",
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
    column=PathNet.dp_role,
)
split_count = CountGraph(
    main_table=page.main_table,
    title="Split Role Distribution",
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
    column=PathNet.dp_split_role,
    filter=PathNet.dp_split_role != "IGNORE",
)
primary_count = CountGraph(
    main_table=page.main_table,
    title="Primary Role Distribution",
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
    column=PathNet.dp_primary_role,
    filter=PathNet.dp_primary_role != "IGNORE",
)
merge_count = CountGraph(
    main_table=page.main_table,
    title="Merge Role Distribution",
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
    column=PathNet.dp_merge_role,
    filter=PathNet.dp_merge_role != "IGNORE",
)
oncoming_count = CountGraph(
    main_table=page.main_table,
    title="Oncoming Distribution",
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
    column=PathNet.dp_points_oncoming,
)
obj_count = ObjCountGraph(
    main_table=page.main_table,
    intersection_switch_id=population_card.intersection_switch_id,
    page_filters_id=filters_agg.final_filter_id,
)
count_columns_dropdown = ColumnsDropdown(main_table=page.main_table, full_grid_row=True)
wildcard_count = CountGraph(
    main_table=page.main_table,
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
    columns_dropdown_id=count_columns_dropdown.component_id,
    full_grid_row=True,
)

obj_to_hide_id = "path_net_conf_mats"
two_datasets_selector = TwoDatasetsSelector(main_table=page.main_table, obj_to_hide_ids=[obj_to_hide_id])
role_conf = ConfMatGraph(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    main_table=two_datasets_selector.main_table,
    page_filters_id=filters_agg.final_filter_id,
    title="Role Classification",
    column=PathNet.dp_role,
    full_grid_row=True,
)
split_conf = ConfMatGraph(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    main_table=two_datasets_selector.main_table,
    page_filters_id=filters_agg.final_filter_id,
    title="Split Role Classification",
    column=PathNet.dp_split_role,
    filter=PathNet.dp_split_role != "IGNORE",
)
primary_conf = ConfMatGraph(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    main_table=two_datasets_selector.main_table,
    page_filters_id=filters_agg.final_filter_id,
    title="Primary Role Classification",
    column=PathNet.dp_primary_role,
    filter=PathNet.dp_primary_role != "IGNORE",
)
merge_conf = ConfMatGraph(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    main_table=two_datasets_selector.main_table,
    page_filters_id=filters_agg.final_filter_id,
    title="Merge Role Classification",
    column=PathNet.dp_merge_role,
    filter=PathNet.dp_merge_role != "IGNORE",
)
oncoming_conf = ConfMatGraph(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    main_table=two_datasets_selector.main_table,
    page_filters_id=filters_agg.final_filter_id,
    title="Oncoming Classification",
    column=PathNet.dp_points_oncoming,
)
conf_columns_dropdown = ColumnsDropdown(main_table=two_datasets_selector.main_table, full_grid_row=True)
wildcard_conf = ConfMatGraph(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    main_table=two_datasets_selector.main_table,
    page_filters_id=filters_agg.final_filter_id,
    columns_dropdown_id=conf_columns_dropdown.component_id,
    full_grid_row=True,
)

frames_modal = FramesModal(
    page_filters_id=filters_agg.final_filter_id,
    triggering_conf_mats=[role_conf, split_conf, primary_conf, merge_conf, oncoming_conf],
    triggering_filters=[data_filters],
)
jump_modal = JumpModal(
    page_filters_id=filters_agg.final_filter_id,
    triggering_conf_mats=[role_conf, split_conf, primary_conf, merge_conf, oncoming_conf],
    triggering_filters=[data_filters],
)

layout = GridGenerator(
    frames_modal,
    jump_modal,
    data_filters,
    obj_count_card,
    population_card,
    filters_agg,
    role_count,
    split_count,
    primary_count,
    merge_count,
    obj_count,
    GridGenerator(
        count_columns_dropdown,
        wildcard_count,
    ),
    GridGenerator(
        two_datasets_selector,
        role_conf,
        split_conf,
        primary_conf,
        merge_conf,
        oncoming_conf,
        GridGenerator(conf_columns_dropdown, wildcard_conf),
        component_id=obj_to_hide_id,
    ),
    warp_sub_objects=False,
).layout()
