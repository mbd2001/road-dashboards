from dataclasses import dataclass

from road_dashboards.road_dump_dashboard.logical_components.constants.init_data_sources import EXISTING_TABLES


@dataclass
class PageProperties:
    """
    Defines the properties of a single page

    Attributes:
            order (int): the relative order of the page (0 is first page, 1 is second, and so on)
            icon (str): the icon of the page in the sidebar
            path (str): page's path
            title (str): path's title
            main_table (str): optional. main table represents by the page (rpw, lb, or so on)
    """

    order: int
    icon: str
    path: str
    title: str
    main_table: str = None

    def __post_init__(self):
        if self.main_table:
            assert self.main_table in EXISTING_TABLES
