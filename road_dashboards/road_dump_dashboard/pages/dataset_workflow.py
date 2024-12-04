from dash import html, register_page

from road_dashboards.road_dump_dashboard.logical_components.constants.page_properties import PageProperties
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.dataset_selector import DatasetSelector
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.objs_count_card import ObjCountCard
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.workflow_table import WorkflowTable
from road_dashboards.road_dump_dashboard.logical_components.multi_page_objects.grid_generator import GridGenerator
from road_dashboards.road_dump_dashboard.table_schemes.meta_data import MetaData

page = PageProperties(order=1, icon="table", path="/workflow_log", title="Workflow Log", main_table="meta_data")
register_page(__name__, **page.__dict__)

dataset_selector = DatasetSelector(main_table=page.main_table)
obj_count_card = ObjCountCard(
    main_table=page.main_table,
    objs_name="Clips",
    datasets_dropdown_id=dataset_selector.main_dataset_dropdown_id,
    distinct_objs=[MetaData.clip_name],
)
workflow_table = WorkflowTable(datasets_dropdown_id=dataset_selector.main_dataset_dropdown_id)


layout = GridGenerator(
    GridGenerator(html.H2("Dataset Selection"), dataset_selector, full_grid_row=False),
    obj_count_card,
    workflow_table,
    warp_sub_objects=False,
).layout()
