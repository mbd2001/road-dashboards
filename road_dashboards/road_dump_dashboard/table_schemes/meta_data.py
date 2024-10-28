from pypika import Case

from road_dashboards.road_dump_dashboard.table_schemes.base import Base, Column


class MetaData(Base):
    gtem_labels_exist: Column = Column("gtem_labels_exist", bool)
    curve_rad_ahead: Column = Column("curve_rad_ahead", float)
    mdbi_country: Column = Column("mdbi_country", str)
    mdbi_road_highway: Column = Column("mdbi_road_highway", str)
    mdbi_road_country: Column = Column("mdbi_road_country", str)
    mdbi_road_city: Column = Column("mdbi_road_city", str)
    mdbi_road_freeway: Column = Column("mdbi_road_freeway", str)
    rightcolor_yellow: Column = Column("rightcolor_yellow", str)
    leftcolor_yellow: Column = Column("leftcolor_yellow", str)
    rightcolor_white: Column = Column("rightcolor_white", str)
    leftcolor_white: Column = Column("leftcolor_white", str)
    rightcolor_blue: Column = Column("rightcolor_blue", str)
    leftcolor_blue: Column = Column("leftcolor_blue", str)
    is_tv_perfect: Column = Column("is_tv_perfect", bool)
    road_type: Case = (
        Case(alias="road_type")
        .when(mdbi_road_highway == True, "highway")
        .when(mdbi_road_country == True, "country")
        .when(mdbi_road_city == True, "urban")
        .when(mdbi_road_freeway == True, "freeway")
        .else_("other")
    )
    lm_color: Case = (
        Case(alias="lm_color")
        .when((rightcolor_yellow == True) & (rightcolor_yellow == True), "yellow")
        .when((rightcolor_white == True) & (rightcolor_white == True), "white")
        .when((rightcolor_blue == True) & (rightcolor_blue == True), "blue")
        .else_("other")
    )
