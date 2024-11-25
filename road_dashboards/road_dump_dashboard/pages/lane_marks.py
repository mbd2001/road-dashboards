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
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.jump_modal import JumpModal
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.obj_count_graph import ObjCountGraph
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.objs_count_card import ObjCountCard
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.population_card import PopulationCard
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.two_datasets_selector import (
    TwoDatasetsSelector,
)
from road_dashboards.road_dump_dashboard.logical_components.multi_page_objects.grid_generator import GridGenerator
from road_dashboards.road_dump_dashboard.table_schemes.lane_marks import LaneMarks

page = PageProperties(order=2, icon="search", path="/lane_marks", title="Lane Marks", main_table="lm_meta_data")
register_page(__name__, **page.__dict__)

data_filters = DataFilters(main_table=page.main_table)
population_card = PopulationCard()
filters_agg = FiltersAggregator(population_card.final_filter_id, data_filters.final_filter_id)

obj_count_card = ObjCountCard(
    main_table=page.main_table,
    objs_name="Lane marks",
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
)
type_count = CountGraph(
    column=LaneMarks.type,
    title="Type Distribution",
    main_table=page.main_table,
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
    full_grid_row=True,
)
color_count = CountGraph(
    column=LaneMarks.color,
    title="Color Distribution",
    main_table=page.main_table,
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
)
role_count = CountGraph(
    column=LaneMarks.role,
    title="Role Distribution",
    main_table=page.main_table,
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
)
vr_hist = CountGraph(
    column=LaneMarks.max_view_range,
    title="Max View Range Distribution (m)",
    main_table=page.main_table,
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
    filter=LaneMarks.max_view_range < 250,
    slider_value=0,
    full_grid_row=True,
)
painted_len_hist = CountGraph(
    column=LaneMarks.dashed_length,
    title="Dashed Painted Length Distribution",
    main_table=page.main_table,
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
    filter=(LaneMarks.type == "dashed") & (LaneMarks.dashed_length[0:20]),
    slider_value=1,
    full_grid_row=True,
)
dashed_width_hist = CountGraph(
    column=LaneMarks.avg_width,
    title="Lane Mark Width Distribution (m)",
    main_table=page.main_table,
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
    filter=(LaneMarks.avg_width > 0) & (LaneMarks.avg_width < 1.5),
    slider_value=2,
    full_grid_row=True,
)
dashed_gap_hist = CountGraph(
    column=LaneMarks.dashed_gap,
    title="Dashed Gap Length Distribution",
    main_table=page.main_table,
    page_filters_id=filters_agg.final_filter_id,
    intersection_switch_id=population_card.intersection_switch_id,
    filter=(LaneMarks.type == "dashed") & (LaneMarks.dashed_length[0:25]),
    slider_value=1,
    full_grid_row=True,
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

obj_to_hide_id = "lane_marks_conf_mats"
two_datasets_selector = TwoDatasetsSelector(main_table=page.main_table, obj_to_hide_ids=[obj_to_hide_id])
type_conf = ConfMatGraph(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    page_filters_id=filters_agg.final_filter_id,
    title="Type Classification",
    main_table=page.main_table,
    column=LaneMarks.type,
    full_grid_row=True,
)
color_conf = ConfMatGraph(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    page_filters_id=filters_agg.final_filter_id,
    title="Color Classification",
    main_table=page.main_table,
    column=LaneMarks.color,
)
role_conf = ConfMatGraph(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    page_filters_id=filters_agg.final_filter_id,
    title="Role Classification",
    main_table=page.main_table,
    column=LaneMarks.role,
)
wildcard_conf = ConfMatGraphWithDropdown(
    main_dataset_dropdown_id=two_datasets_selector.main_dataset_dropdown_id,
    secondary_dataset_dropdown_id=two_datasets_selector.secondary_dataset_dropdown_id,
    page_filters_id=filters_agg.final_filter_id,
    main_table=page.main_table,
)
frames_modal = FramesModal(
    page_filters_id=filters_agg.final_filter_id,
    triggering_conf_mats=[type_conf, color_conf, role_conf],
    triggering_dropdown_conf_mats=[wildcard_conf],
    triggering_filters=[data_filters],
)
jump_modal = JumpModal(
    page_filters_id=filters_agg.final_filter_id,
    triggering_conf_mats=[type_conf, color_conf, role_conf],
    triggering_dropdown_conf_mats=[wildcard_conf],
    triggering_filters=[data_filters],
)

layout = GridGenerator(
    frames_modal,
    jump_modal,
    data_filters,
    obj_count_card,
    population_card,
    filters_agg,
    type_count,
    color_count,
    role_count,
    vr_hist,
    painted_len_hist,
    dashed_width_hist,
    dashed_gap_hist,
    obj_count,
    wildcard_count,
    GridGenerator(
        two_datasets_selector,
        type_conf,
        color_conf,
        role_conf,
        wildcard_conf,
        component_id=obj_to_hide_id,
    ),
    warp_sub_objects=False,
).layout()
