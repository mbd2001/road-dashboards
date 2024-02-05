import pandas as pd
from dash import html, register_page, dcc, Output, Input, callback, no_update

from road_eval_dashboard.components.catalog_table import generate_catalog_layout, run_eval_db_manager
from road_eval_dashboard.components.components_ids import CATALOG, RUN_EVAL_CATALOG
from road_eval_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper
from road_eval_dashboard.components.page_properties import PageProperties

extra_properties = PageProperties("home")
register_page(__name__, path="/home", name="Home", order=0, **extra_properties.__dict__)


layout = html.Div(
    [html.H1("RoadE2E Metrics Dashboard", className="mb-5"), card_wrapper([loading_wrapper(dcc.Store(id=CATALOG), is_full_screen=True), generate_catalog_layout()])]
)

@callback(
    Output(CATALOG, "data"),
    Output(RUN_EVAL_CATALOG, "data"),
    Input(CATALOG, "data"),
    background=True,
)
def init_catalog(catalog):
    if catalog is None:
        catalog_data = pd.DataFrame(run_eval_db_manager.scan()).drop("batches", axis=1)
        catalog_data_dict = catalog_data.to_dict("records")
        return catalog_data_dict, catalog_data_dict
    return no_update, no_update


