from dataclasses import dataclass


@dataclass
class PageProperties:
    """
    Defines the properties of a single page

    Attributes:
            order (int):
            icon (str):
            path (str):
            title (str):
            objs_name (str): optional.
            main_table (str): optional.
            meta_data_table (str): optional.

    """

    order: int
    icon: str
    path: str
    title: str
    objs_name: str = None
    main_table: str = None
    meta_data_table: str = None
