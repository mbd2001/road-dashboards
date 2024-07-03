from dataclasses import dataclass


@dataclass
class PageProperties:
    order: int
    icon: str
    path: str
    title: str
    objs_name: str = None
    main_table: str = None
    meta_data_table: str = None
