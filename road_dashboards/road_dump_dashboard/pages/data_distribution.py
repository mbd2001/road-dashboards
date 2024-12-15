from dash import html, register_page

from road_dashboards.road_dump_dashboard.logical_components.constants.page_properties import PageProperties
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.boosting_control import BoostingControl
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.data_filters import DataFilters
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.dataset_selector import DatasetSelector
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.filters_aggregator import FiltersAggregator
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.objs_count_card import ObjCountCard
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.population_card import PopulationCard
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.scenes_pie import ScenesPie
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.scenes_table import ScenesTable
from road_dashboards.road_dump_dashboard.logical_components.multi_page_objects.grid_generator import GridGenerator
from road_dashboards.road_dump_dashboard.table_schemes.scenes import (
    CA_SCENES,
    CURVES,
    DRIVING_CONDITIONS,
    LM_COLORS,
    LM_TYPES,
    ROAD_EVENTS,
    SENSORS,
)

page = PageProperties(
    order=1, icon="bell", path="/data_distribution", title="Data Distribution", main_table="meta_data"
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

dataset_selector = DatasetSelector(main_table=page.main_table)
scenes = [LM_TYPES, LM_COLORS, DRIVING_CONDITIONS, CURVES, ROAD_EVENTS, SENSORS, CA_SCENES]
scenes_tables = [
    ScenesTable(
        datasets_dropdown_id=dataset_selector.main_dataset_dropdown_id,
        scenes=scene,
        page_filters_id=filters_agg.final_filter_id,
    )
    for scene in scenes
]
boosting_control = BoostingControl(
    datasets_dropdown_id=dataset_selector.main_dataset_dropdown_id,
    population_dropdown_id=population_card.populations_dropdown_id,
    page_filters_id=filters_agg.final_filter_id,
)
scene_pies = [
    ScenesPie(
        datasets_dropdown_id=dataset_selector.main_dataset_dropdown_id,
        population_dropdown_id=population_card.populations_dropdown_id,
        batches_table_id=boosting_control.batches_table_id,
        scenes=scene,
        page_filters_id=filters_agg.final_filter_id,
    )
    for scene in scenes
]

layout = GridGenerator(
    data_filters,
    filters_agg,
    obj_count_card,
    GridGenerator(html.H3("Population"), population_card, full_grid_row=False),
    GridGenerator(
        dataset_selector,
        *scenes_tables,
        boosting_control,
        *scene_pies,
    ),
    warp_sub_objects=False,
).layout()
