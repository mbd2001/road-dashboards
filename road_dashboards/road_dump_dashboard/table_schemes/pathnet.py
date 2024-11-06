from road_dashboards.road_dump_dashboard.table_schemes.base import Base, Column


class PathNet(Base):
    dp_points: Column = Column("dp_points", list[float])
    dv_dp_points: Column = Column("dv_dp_points", list[float])
    dp_points_oncoming: Column = Column("dp_points_oncoming", str)
    dp_role: Column = Column("dp_role", str)
    dp_split_role: Column = Column("dp_split_role", str)
    dp_primary_role: Column = Column("dp_primary_role", str)
    dp_merge_role: Column = Column("dp_merge_role", str)
