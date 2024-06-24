from dataclasses import dataclass, field

from dash import html

from road_dashboards.road_dump_dashboard.components.common_pages_layout import base_dataset_statistics, data_filters
from road_dashboards.road_dump_dashboard.components.constants.graphs_properties import GRAPHS_PER_PAGE
from road_dashboards.road_dump_dashboard.components.graph_wrappers import conf_mats_collection, count_graphs_collection


@dataclass
class PageProperties:
    order: int
    icon: str
    path: str
    title: str
    objs_name: str = None
    main_table: str = None
    meta_data_table: str = None
    labels_table: str = None
    extra_callable_layouts: list = field(default_factory=list)

    def __post_init__(self):
        if not self.labels_table:
            self.labels_table = self.main_table

    def get_page_layout(self):
        page_graphs = GRAPHS_PER_PAGE.get(self.path.strip("/"))
        count_graphs = page_graphs.get("count_graphs") if page_graphs else None
        conf_mat_graphs = page_graphs.get("conf_mat_graphs") if page_graphs else None

        extra_callable_layouts = [func() for func in self.extra_callable_layouts]
        page_layout = [
            html.H1(self.title, className="mb-5"),
            data_filters.layout if self.main_table else None,
            base_dataset_statistics.layout(self.objs_name) if self.objs_name else None,
            count_graphs_collection.layout(self.meta_data_table, count_graphs) if count_graphs else None,
            conf_mats_collection.layout(conf_mat_graphs) if conf_mat_graphs else None,
            *extra_callable_layouts,
        ]
        return html.Div(page_layout)
