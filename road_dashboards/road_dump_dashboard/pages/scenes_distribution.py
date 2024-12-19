import dash_bootstrap_components as dbc
from dash import html, register_page

from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import META_DATA
from road_dashboards.road_dump_dashboard.logical_components.constants.layout_wrappers import card_wrapper
from road_dashboards.road_dump_dashboard.logical_components.constants.page_properties import PageProperties
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.boosting_control import BoostingControl
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.data_filters import DataFilters
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.dataset_selector import DatasetSelector
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.filters_aggregator import FiltersAggregator
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.frames_modal import FramesModal
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.jump_modal import JumpModal
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.objs_count_card import ObjCountCard
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.population_card import PopulationCard
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.scenes_pie import ScenesPie
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.scenes_table import ScenesTable
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.switch import Switch
from road_dashboards.road_dump_dashboard.logical_components.multi_page_objects.grid_generator import GridGenerator
from road_dashboards.road_dump_dashboard.table_schemes.scenes import (
    CA_SCENES,
    CAMERAS,
    CURVES,
    DRIVING_CONDITIONS,
    EXTRA_CURVES,
    EXTRA_LM_TYPES,
    LM_COLORS,
    LM_TYPES,
    ROAD_EVENTS,
    SENSORS,
)

page = PageProperties(
    order=1, icon="bell", path="/scenes_distribution", title="Scenes Distribution", main_table=META_DATA
)
register_page(__name__, **page.__dict__)


data_filters = DataFilters(main_table=page.main_table)
population_card = PopulationCard()
filters_agg = FiltersAggregator(population_card.final_filter_id, data_filters.final_filter_id)
obj_count_card = ObjCountCard(
    main_table=page.main_table,
    objs_name="Frames",
    page_filters_id=filters_agg.final_filter_id,
)

dataset_selector = DatasetSelector(main_table=page.main_table, full_grid_row=False)
insufficient_switch = Switch(label="Insufficient Scenes", full_grid_row=False)

categories_partition = [
    [LM_TYPES, EXTRA_LM_TYPES],
    [LM_COLORS],
    [DRIVING_CONDITIONS],
    [CURVES, EXTRA_CURVES],
    [ROAD_EVENTS],
    [SENSORS, CAMERAS],
    [CA_SCENES],
]
accordion_items = [
    dbc.AccordionItem(
        ScenesTable(
            datasets_dropdown_id=dataset_selector.main_dataset_dropdown_id,
            scenes_categories=scene_categories,
            page_filters_id=filters_agg.final_filter_id,
            insufficient_switch_id=insufficient_switch.component_id,
        ).layout(),
        title=scene_categories[0].name,
        item_id=scene_categories[0].name,
        className="slim-accordion",
    )
    for scene_categories in categories_partition
]
tables_accordion = dbc.Accordion(
    accordion_items,
    always_open=True,
    active_item=[accordion_item.item_id for accordion_item in accordion_items],
    className="mt-5",
)

boosting_control = BoostingControl(
    datasets_dropdown_id=dataset_selector.main_dataset_dropdown_id,
    population_dropdown_id=population_card.populations_dropdown_id,
    page_filters_id=filters_agg.final_filter_id,
)
pie_categories = [LM_TYPES, LM_COLORS, DRIVING_CONDITIONS, CURVES, ROAD_EVENTS, SENSORS, CA_SCENES]
scene_pies = [
    ScenesPie(
        datasets_dropdown_id=dataset_selector.main_dataset_dropdown_id,
        population_dropdown_id=population_card.populations_dropdown_id,
        batches_table_id=boosting_control.batches_table_id,
        scene_category=scene,
        page_filters_id=filters_agg.final_filter_id,
    )
    for scene in pie_categories
]

frames_modal = FramesModal(page_filters_id=filters_agg.final_filter_id, triggering_filters=[data_filters])
jump_modal = JumpModal(page_filters_id=filters_agg.final_filter_id, triggering_filters=[data_filters])

layout = GridGenerator(
    frames_modal,
    jump_modal,
    data_filters,
    filters_agg,
    obj_count_card,
    GridGenerator(html.H3("Population"), population_card, full_grid_row=False),
    GridGenerator(dataset_selector, insufficient_switch, tables_accordion).layout(),
    card_wrapper(
        dbc.Tabs(
            [
                dbc.Tab(GridGenerator(boosting_control, warp_sub_objects=False).layout(), label="Boosting Control"),
                dbc.Tab(
                    GridGenerator(*scene_pies, warp_sub_objects=False).layout(), label="Weighted Data Distribution"
                ),
            ]
        )
    ),
    warp_sub_objects=False,
).layout()
