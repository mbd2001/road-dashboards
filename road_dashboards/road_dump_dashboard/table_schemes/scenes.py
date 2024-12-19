from dataclasses import dataclass
from functools import reduce
from operator import add

from pypika import Case, Criterion, functions
from pypika.terms import Function, Term

from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import META_DATA
from road_dashboards.road_dump_dashboard.logical_components.constants.init_data_sources import EXISTING_TABLES
from road_dashboards.road_dump_dashboard.table_schemes.base import Column
from road_dashboards.road_dump_dashboard.table_schemes.meta_data import MetaData


@dataclass
class Scene:
    name: str
    obj_conditions: list[Criterion]
    required_objects: int = 0

    def definition(self) -> str:
        return str(reduce(add, self.obj_conditions))

    def weighted_sum(self, frame_weight: int | Term) -> Function:
        weighted_case = reduce(
            add, [Case().when(condition, frame_weight).else_(0) for condition in self.obj_conditions]
        )
        return functions.Sum(weighted_case).as_(self.name)

    def terms(self) -> list[Column]:
        return [col for cond in self.obj_conditions for col in cond.find_(Column)]


@dataclass
class ScenesCategory:
    name: str
    scenes: list[Scene]
    table: str = META_DATA

    def __post_init__(self):
        scene_len = len(self.scenes[0].obj_conditions)
        assert all(
            len(scene.obj_conditions) == scene_len for scene in self.scenes
        ), "inconsistent instance_conditions len between scenes, you might want to check that they represents the same obj type (frame, lm, dp, etc.)"
        assert self.table in EXISTING_TABLES, f"ScenesCategory '{self.name}' table is not in existing tables"

    def other(self) -> Scene:
        matched_conditions = [i for i in zip(*[scene.obj_conditions for scene in self.scenes])]
        obj_conditions = [~Criterion.any(conditions) for conditions in matched_conditions]
        return Scene("other", obj_conditions)

    def weighted_sums(self, frame_weight: int | Term, include_other: bool) -> list[Function]:
        scenes = self.scenes if not include_other else self.scenes + [self.other()]
        return [scene.weighted_sum(frame_weight) for scene in scenes]

    def terms(self) -> list[Column]:
        return [col for scene in self.scenes for col in scene.terms()]


LM_TYPES: ScenesCategory = ScenesCategory(
    "Lane Mark Types",
    [
        Scene(
            "DecelerationSolid",
            [MetaData.righttype_decelerationsolid == True, MetaData.lefttype_decelerationsolid == True],
            20000,
        ),
        Scene(
            "DecelerationDashed",
            [MetaData.righttype_decelerationdashed == True, MetaData.lefttype_decelerationdashed == True],
            20000,
        ),
        Scene("Deceleration", [MetaData.righttype_deceleration == True, MetaData.lefttype_deceleration == True], 20000),
        Scene("dashed", [MetaData.righttype_dashed == True, MetaData.lefttype_dashed == True], 20000),
        Scene("solid", [MetaData.righttype_solid == True, MetaData.lefttype_solid == True], 20000),
        Scene("bottsdots", [MetaData.righttype_botsdots == True, MetaData.lefttype_botsdots == True], 20000),
        Scene("dashedsolid", [MetaData.righttype_dashedsolid == True, MetaData.lefttype_dashedsolid == True], 20000),
        Scene("soliddashed", [MetaData.righttype_soliddashed == True, MetaData.lefttype_soliddashed == True], 20000),
        Scene("dasheddashed", [MetaData.righttype_dasheddashed == True, MetaData.lefttype_dasheddashed == True], 20000),
        Scene("solidsolid", [MetaData.righttype_solidsolid == True, MetaData.lefttype_solidsolid == True], 20000),
        Scene("snowonlane", [MetaData.righttype_snowonlane == True, MetaData.lefttype_snowonlane == True], 20000),
        Scene("fence", [MetaData.righttype_fence == True, MetaData.lefttype_fence == True], 20000),
        Scene("otherre", [MetaData.righttype_otherre == True, MetaData.lefttype_otherre == True], 20000),
        Scene("curb", [MetaData.righttype_curb == True, MetaData.lefttype_curb == True], 20000),
        Scene("barrier", [MetaData.righttype_barrier == True, MetaData.lefttype_barrier == True], 20000),
        Scene("grass", [MetaData.righttype_grass == True, MetaData.lefttype_grass == True], 20000),
    ],
)

EXTRA_LM_TYPES: ScenesCategory = ScenesCategory(
    "Lane Mark Types",
    [
        Scene("wide_lane_mark", [(MetaData.max_lm_width_avg[0.35:0.60]) & (MetaData.dist_to_hwe > 40)], 10000),
        Scene(
            "japanese_poles",
            [
                (MetaData.mdbi_country == "Japan")
                & (MetaData.safetyzoneleft == False)
                & (MetaData.safetyzoneright == False)
                & ((MetaData.dist_to_polesleft < 20) & (MetaData.dist_from_polesright < 20))
            ],
            10000,
        ),
        Scene(
            "china_bus_lane", [(MetaData.mdbi_country == "China") & (MetaData.rightcolor_yellowwhite == True)], 10000
        ),
        # Scene("HOV", [""], 10000),
    ],
)

LM_COLORS: ScenesCategory = ScenesCategory(
    "Lane Mark Colors",
    [
        Scene("yellow", [MetaData.rightcolor_yellow == True, MetaData.leftcolor_yellow == True], 20000),
        Scene("blue", [MetaData.rightcolor_blue == True, MetaData.leftcolor_blue == True], 20000),
        Scene("white", [MetaData.rightcolor_white == True, MetaData.leftcolor_white == True], 20000),
        # Scene("contrast_lane_marks", [""], 10000),
    ],
)


DRIVING_CONDITIONS: ScenesCategory = ScenesCategory(
    "Driving Conditions",
    [
        Scene(
            "rainy_night",
            [
                (MetaData.mdbi_time_of_day == "Night")
                & ((MetaData.rain == True) | (MetaData.rainy == True) | (MetaData.wetroad == True))
            ],
            10000,
        ),
        Scene("low_sun", [(MetaData.suninimage == True) | (MetaData.lowsun == True)], 10000),
        Scene(
            "guard_rail_shadows",
            [(MetaData.dist_to_shadowsguardrail_hostleft < 30) | (MetaData.dist_to_shadowsguardrail_hostright < 30)],
            10000,
        ),
        Scene(
            "dashed_shape_guard_rail_shadows",
            [
                (MetaData.dist_to_shadowguardraildashed_hostleft < 30)
                | (MetaData.dist_to_shadowguardraildashed_hostright < 30)
            ],
            10000,
        ),
        Scene(
            "diagonal_guard_rail_shadows",
            [(MetaData.dist_to_diagonalshadow_hostleft < 30) | (MetaData.dist_to_diagonalshadow_hostright < 30)],
            10000,
        ),
        # Scene([""], "sun_ray", 10000),
    ],
)


CURVES: ScenesCategory = ScenesCategory(
    "Curves",
    [
        Scene(
            "strong_curves", [(MetaData.curve_rad_ahead_gt_120 >= 0) & (MetaData.curve_rad_ahead_gt_120 < 250)], 10000
        ),
        Scene(
            "medium_curves", [(MetaData.curve_rad_ahead_gt_120 >= 250) & (MetaData.curve_rad_ahead_gt_120 < 500)], 10000
        ),
        Scene(
            "light_curves", [(MetaData.curve_rad_ahead_gt_120 >= 500) & (MetaData.curve_rad_ahead_gt_120 < 800)], 10000
        ),
    ],
)

EXTRA_CURVES: ScenesCategory = ScenesCategory(
    "Curves",
    [
        Scene("crest_seg", [MetaData.vertical_change_50m > 1], 10000),
        Scene("ramp", [MetaData.ramp == True], 10000),
        # Scene([""], "hilly_road_curves", 10000),
    ],
)

ROAD_EVENTS: ScenesCategory = ScenesCategory(
    "Events",
    [
        Scene(
            "marked",
            [
                ((MetaData.dist_to_hwemarked_hostleft < 60) & (MetaData.dist_to_hwemarked_hostleft > 0))
                | ((MetaData.dist_to_hwemarked_hostright < 60) & (MetaData.dist_to_hwemarked_hostright > 0))
            ],
            10000,
        ),
        Scene(
            "semimarked",
            [
                ((MetaData.dist_to_hwesemimarked_hostleft < 60) & (MetaData.dist_to_hwesemimarked_hostleft > 0))
                | ((MetaData.dist_to_hwesemimarked_hostright < 60) & (MetaData.dist_to_hwesemimarked_hostright > 0))
            ],
            10000,
        ),
        Scene(
            "unmarked",
            [
                ((MetaData.dist_to_hweunmarked_hostleft < 60) & (MetaData.dist_to_hweunmarked_hostleft > 0))
                | ((MetaData.dist_to_hweunmarked_hostright < 60) & (MetaData.dist_to_hweunmarked_hostright > 0))
            ],
            10000,
        ),
        Scene("merge", [MetaData.dist_to_lanemerge < 60], 10000),
        Scene(
            "german_hatched",
            [
                ((MetaData.mdbi_country == "Germany") | (MetaData.mdbi_country == "Unknown"))
                & (MetaData.dist_to_lanemerge < 40)
                & (MetaData.dist_to_hatchedarea < 60)
                & (MetaData.dist_to_constarea_true > 100)
                & (MetaData.dist_to_constarea_optional > 100)
                & (MetaData.intersection == False)
            ],
            10000,
        ),
        Scene("Roundabout", [MetaData.dist_to_roundabout < 60], 10000),
        Scene("Junction", [MetaData.dist_to_intersection < 60], 10000),
        Scene(
            "lane_change",
            [(MetaData.dist_to_rightcrossing_changinglanes < 20) | (MetaData.dist_to_leftcrossing_changinglanes < 20)],
            10000,
        ),
    ],
)


SENSORS: ScenesCategory = ScenesCategory(
    "Sensors",
    [
        Scene("Mono8", [MetaData.is_eyeq6 == False], 10000),
        Scene(
            "EyeQ6",
            [(MetaData.is_eyeq6 == True) & (MetaData.image_sensor_type.notin(["SONY_IMX324", "SONY_IMX728"]))],
            10000,
        ),
        Scene(
            "EyeQ6_sony",
            [(MetaData.is_eyeq6 == True) & (MetaData.image_sensor_type.isin(["SONY_IMX324", "SONY_IMX728"]))],
            10000,
        ),
    ],
)

CAMERAS: ScenesCategory = ScenesCategory(
    "Cameras",
    [
        Scene("high_camera", [MetaData.camh > 1.5], 10000),
    ],
)

CA_SCENES: ScenesCategory = ScenesCategory(
    "CA",
    [
        Scene("CA", [(MetaData.dist_to_constarea_true < 40) & (MetaData.dist_to_constarea_optional != 0)], 10000),
        Scene(
            "CA_yellow",
            [
                ((MetaData.dist_to_constarea_true < 40) | (MetaData.dist_to_constarea_optional < 40))
                & ((MetaData.is_yellow_right == True) | (MetaData.is_yellow_left == True))
            ],
            10000,
        ),
        Scene(
            "CA_right_left_conesbarrels",
            [
                ((MetaData.righttype_conesbarrels == True) & (MetaData.dp_boundary_right_type_has_re == True))
                | ((MetaData.lefttype_conesbarrels == True) & (MetaData.dp_boundary_left_type_has_re == True))
            ],
            10000,
        ),
        Scene("CA_crossing", [MetaData.dist_to_cacrossing < 60], 10000),
    ],
)
