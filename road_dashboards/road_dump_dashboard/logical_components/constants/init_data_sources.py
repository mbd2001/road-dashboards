from road_dump_dashboard.logical_components.constants.components_ids import META_DATA
from road_dump_dashboard.table_schemes.base import Base
from road_dump_dashboard.table_schemes.lane_marks import LaneMarks
from road_dump_dashboard.table_schemes.meta_data import MetaData
from road_dump_dashboard.table_schemes.pathnet import PathNet

EXISTING_TABLES: dict[str, type[Base]] = {META_DATA: MetaData, "lm_meta_data": LaneMarks, "rpw_meta_data": PathNet}


def init_tables(dataset_names: list[str], **kwargs) -> list[list[Base] | None]:
    table_instances = [
        get_tables_from_type(table_type, table_class, dataset_names, **kwargs)
        for table_type, table_class in EXISTING_TABLES.items()
    ]
    return table_instances


def get_tables_from_type(
    table_type: str, table_class: type[Base], dataset_names: list[str], **kwargs
) -> list[Base] | None:
    table_names = kwargs.get(f"{table_type}_table", [""] * len(dataset_names))
    tables = [
        table_class(table_name, dataset_name)
        for table_name, dataset_name in zip(table_names, dataset_names)
        if table_name
    ]
    if len(tables) != len(dataset_names):
        return None

    return tables
