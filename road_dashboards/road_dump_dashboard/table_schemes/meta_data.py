from pypika import Case

from road_dashboards.road_dump_dashboard.table_schemes.base import Base, Column


class MetaData(Base):
    curve_rad_ahead: Column = Column("curve_rad_ahead", float)
    gtem_labels_exist: Column = Column("gtem_labels_exist", bool)
    mdbi_country: Column = Column("mdbi_country", bool)
    mdbi_road_highway: Column = Column("mdbi_road_highway", bool)
    mdbi_road_country: Column = Column("mdbi_road_country", bool)
    mdbi_road_city: Column = Column("mdbi_road_city", bool)
    mdbi_road_freeway: Column = Column("mdbi_road_freeway", bool)
    rightcolor_yellow: Column = Column("rightcolor_yellow", bool)
    leftcolor_yellow: Column = Column("leftcolor_yellow", bool)
    rightcolor_white: Column = Column("rightcolor_white", bool)
    leftcolor_white: Column = Column("leftcolor_white", bool)
    rightcolor_blue: Column = Column("rightcolor_blue", bool)
    leftcolor_blue: Column = Column("leftcolor_blue", bool)
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
