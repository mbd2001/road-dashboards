from dataclasses import dataclass


@dataclass
class PageProperties:
    """
    Defines the properties of a single page

    Attributes:
            order (int): the relative order of the page (0 is first page, 1 is second, and so on)
            icon (str): the icon of the page in the sidebar
            path (str): page's path
            title (str): path's title
            objs_name (str): optional. the name of the objects that the page represent
            main_table (str): optional. main table represents by the page (rpw, lb, or so on)
            meta_data_table (str): optional. the meta data table represents by the page

    """

    order: int
    icon: str
    path: str
    title: str
    objs_name: str = None
    main_table: str = None
    meta_data_table: str = None
