from road_dashboards.road_dump_dashboard.table_schemes.base import Base, Column


class LaneMarks(Base):
    half_width: Column = Column("half_width", list[float], drawable=True)
    pos: Column = Column("pos", list[float], drawable=True)
    pos_x: Column = Column("pos_x", list[float], drawable=True)
    pos_z: Column = Column("pos_z", list[float], drawable=True)
    ds_y_off: Column = Column("ds_y_off", list[float])
    de_y_off: Column = Column("de_y_off", list[float])
    role: Column = Column("role", str, drawable=True)
    type: Column = Column("type", str, drawable=True)
    color: Column = Column("color", str, drawable=True)
    avg_width: Column = Column("avg_width", float)
    max_width: Column = Column("max_width", float)
    dashed_length: Column = Column("dashed_length", float)
    dashed_gap: Column = Column("dashed_gap", float)
    max_view_range: Column = Column("max_view_range", float)
    min_view_range: Column = Column("min_view_range", float)
