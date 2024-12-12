from dataclasses import dataclass

from pypika import Case, Criterion, functions
from pypika.terms import Term

from road_dashboards.road_dump_dashboard.table_schemes.lane_marks import LaneMarks
from road_dashboards.road_dump_dashboard.table_schemes.meta_data import MetaData


@dataclass
class Scene:
    definition: Criterion
    name: str
    required_frames: int

    def count(self) -> Term:
        return functions.Sum(Case().when(self.definition, 1).else_(0)).as_(self.name)


LM_TYPES: list[Scene] = [
    Scene(
        (MetaData.righttype_decelerationsolid == True) | (MetaData.lefttype_decelerationsolid == True),
        "DecelerationSolid",
        10000,
    ),
    Scene(
        (MetaData.righttype_decelerationdashed == True) | (MetaData.lefttype_decelerationdashed == True),
        "DecelerationDashed",
        10000,
    ),
    Scene((MetaData.righttype_deceleration == True) | (MetaData.lefttype_deceleration == True), "Deceleration", 10000),
    Scene((MetaData.righttype_botsdots == True) | (MetaData.lefttype_botsdots == True), "bottsdots", 10000),
    Scene((MetaData.righttype_dashedsolid == True) | (MetaData.lefttype_dashedsolid == True), "dashedsolid", 10000),
    Scene((MetaData.righttype_soliddashed == True) | (MetaData.lefttype_soliddashed == True), "soliddashed", 10000),
    Scene((MetaData.righttype_dasheddashed == True) | (MetaData.lefttype_dasheddashed == True), "dasheddashed", 10000),
    Scene((MetaData.righttype_solidsolid == True) | (MetaData.lefttype_solidsolid == True), "solidsolid", 10000),
    Scene((MetaData.max_lm_width_avg[0.35:0.60]) & (MetaData.dist_to_hwe > 40), "wide_lane_mark", 10000),
    Scene(
        (MetaData.mdbi_country == "Japan")
        & (MetaData.safetyzoneleft == False)
        & (MetaData.safetyzoneright == False)
        & ((MetaData.dist_to_polesleft < 20) & (MetaData.dist_from_polesright < 20)),
        "japanese_poles",
        10000,
    ),
    Scene((MetaData.mdbi_country == "China") & (MetaData.rightcolor_yellowwhite == True), "china_bus_lane", 10000),
    # Scene("", "HOV", 10000),
]


LM_COLORS: list[Scene] = [
    Scene((MetaData.rightcolor_yellow == True) | (MetaData.leftcolor_yellow == True), "yellow", 10000),
    Scene((MetaData.rightcolor_blue == True) | (MetaData.leftcolor_blue == True), "blue", 10000),
    Scene((MetaData.rightcolor_white == True) | (MetaData.leftcolor_white == True), "white", 10000),
    # Scene("", "contrast_lane_marks", 10000),
]


# LM_COLORS: list[Scene] = [
#     Scene(LaneMarks.color == "yellow", "yellow", 10000),
#     Scene(LaneMarks.color == "blue", "blue", 10000),
#     Scene(LaneMarks.color == "white", "white", 10000),
#     # Scene("", "contrast_lane_marks", 10000),
# ]


DRIVING_CONDITIONS: list[Scene] = [
    Scene(
        (MetaData.mdbi_time_of_day == "Night")
        & ((MetaData.rain == True) | (MetaData.rainy == True) | (MetaData.wetroad == True)),
        "rainy_night",
        10000,
    ),
    Scene((MetaData.suninimage == True) | (MetaData.lowsun == True), "low_sun", 10000),
    Scene(
        (MetaData.dist_to_shadowsguardrail_hostleft < 30) | (MetaData.dist_to_shadowsguardrail_hostright < 30),
        "guard_rail_shadows",
        10000,
    ),
    Scene(
        (MetaData.dist_to_shadowguardraildashed_hostleft < 30)
        | (MetaData.dist_to_shadowguardraildashed_hostright < 30),
        "dashed_shape_guard_rail_shadows",
        10000,
    ),
    Scene(
        (MetaData.dist_to_diagonalshadow_hostleft < 30) | (MetaData.dist_to_diagonalshadow_hostright < 30),
        "diagonal_guard_rail_shadows",
        10000,
    ),
    # Scene("", "sun_ray", 10000),
]


CURVES: list[Scene] = [
    Scene(MetaData.vertical_change_50m > 1, "crest_seg", 10000),
    Scene((MetaData.curve_rad_ahead_150 >= 0) & (MetaData.curve_rad_ahead_150 < 250), "strong_curves", 10000),
    Scene((MetaData.curve_rad_ahead_150 >= 250) & (MetaData.curve_rad_ahead_150 < 500), "medium_curves", 10000),
    Scene((MetaData.curve_rad_ahead_150 >= 500) & (MetaData.curve_rad_ahead_150 < 800), "light_curves", 10000),
    Scene(MetaData.ramp == True, "ramp", 10000),
    # Scene("", "hilly_road_curves", 10000),
]


ROAD_EVENTS: list[Scene] = [
    Scene(
        ((MetaData.dist_to_hwemarked_hostleft < 60) & (MetaData.dist_to_hwemarked_hostleft > 0))
        | ((MetaData.dist_to_hwemarked_hostright < 60) & (MetaData.dist_to_hwemarked_hostright > 0)),
        "marked",
        10000,
    ),
    Scene(
        ((MetaData.dist_to_hwesemimarked_hostleft < 60) & (MetaData.dist_to_hwesemimarked_hostleft > 0))
        | ((MetaData.dist_to_hwesemimarked_hostright < 60) & (MetaData.dist_to_hwesemimarked_hostright > 0)),
        "semimarked",
        10000,
    ),
    Scene(
        ((MetaData.dist_to_hweunmarked_hostleft < 60) & (MetaData.dist_to_hweunmarked_hostleft > 0))
        | ((MetaData.dist_to_hweunmarked_hostright < 60) & (MetaData.dist_to_hweunmarked_hostright > 0)),
        "unmarked",
        10000,
    ),
    Scene(MetaData.dist_to_lanemerge < 60, "merge", 10000),
    Scene(
        ((MetaData.mdbi_country == "Germany") | (MetaData.mdbi_country == "Unknown"))
        & (MetaData.dist_to_lanemerge < 40)
        & (MetaData.dist_to_hatchedarea < 60)
        & (MetaData.dist_to_constarea_true > 100)
        & (MetaData.dist_to_constarea_optional > 100)
        & (MetaData.intersection == False),
        "german_hatched",
        10000,
    ),
    Scene(MetaData.dist_to_roundabout < 60, "Roundabout", 10000),
    Scene(MetaData.dist_to_intersection < 60, "Junction", 10000),
    Scene(
        (MetaData.dist_to_rightcrossing_changinglanes < 20) | (MetaData.dist_to_leftcrossing_changinglanes < 20),
        "lane_change",
        10000,
    ),
]


SENSORS: list[Scene] = [
    # Scene(MetaData.ramp == True, "Mono8", 10000),
    Scene(MetaData.is_eyeq6 == True, "EyeQ6", 10000),
    Scene(
        (MetaData.is_eyeq6 == True) & (MetaData.image_sensor_type.isin(["SONY_IMX324", "SONY_IMX728"])),
        "EyeQ6_sony",
        10000,
    ),
    Scene(MetaData.camh > 1.5, "high_camera", 10000),
]


CA_SCENES: list[Scene] = [
    Scene(MetaData.dist_to_constarea_optional != 0, "CA", 10000),
    Scene(
        ((MetaData.dist_to_constarea_optional < 40) | (MetaData.dist_to_constarea_true < 40))
        & ((MetaData.is_yellow_right == True) | (MetaData.is_yellow_left == True)),
        "CA_yellow",
        10000,
    ),
    Scene(
        ((MetaData.righttype_conesbarrels == True) & (MetaData.dp_boundary_right_type_has_re == True))
        | ((MetaData.lefttype_conesbarrels == True) & (MetaData.dp_boundary_left_type_has_re == True)),
        "CA_right_left_conesbarrels",
        10000,
    ),
    Scene(MetaData.dist_to_cacrossing < 60, "CA_crossing", 10000),
]
