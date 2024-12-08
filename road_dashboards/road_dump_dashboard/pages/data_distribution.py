from dash import html, register_page

from road_dashboards.road_dump_dashboard.logical_components.constants.page_properties import PageProperties
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.data_filters import DataFilters
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.dataset_selector import DatasetSelector
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.filters_aggregator import FiltersAggregator
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.population_card import PopulationCard
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.scenes_table import ScenesTable
from road_dashboards.road_dump_dashboard.logical_components.multi_page_objects.grid_generator import GridGenerator

page = PageProperties(
    order=1, icon="bell", path="/data_distribution", title="Data Distribution", main_table="meta_data"
)
register_page(__name__, **page.__dict__)

data_filters = DataFilters(main_table=page.main_table)
population_card = PopulationCard()
filters_agg = FiltersAggregator(population_card.final_filter_id, data_filters.final_filter_id)
dataset_selector = DatasetSelector(main_table=page.main_table)
scenes_table = ScenesTable(
    datasets_dropdown_id=dataset_selector.main_dataset_dropdown_id,
    page_filters_id=filters_agg.final_filter_id,
)

layout = GridGenerator(
    data_filters,
    filters_agg,
    GridGenerator(html.H3("Dataset Selection"), dataset_selector, full_grid_row=False),
    GridGenerator(html.H3("Population"), population_card, full_grid_row=False),
    scenes_table,
    warp_sub_objects=False,
).layout()
