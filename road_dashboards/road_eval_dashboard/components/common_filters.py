from road_dashboards.road_eval_dashboard.components.queries_manager import INTERSTING_FILTERS_DIST_TO_CHECK

ROAD_TYPE_FILTERS = {
    "highway": "mdbi_road_highway = TRUE OR mdbi_road_freeway = TRUE",
    "country": "mdbi_road_country = TRUE",
    "urban": "mdbi_road_city = TRUE",
}

PATHNET_ROAD_FILTERS = {
    "highway": "highway = TRUE",
    "country": "country = TRUE",
    "urban": "urban = TRUE",
    "other": "(highway OR country OR urban) = FALSE",
    "all": "(urban = TRUE or urban = FALSE)",
}

LANE_MARK_TYPE_FILTERS = {
    "dashed": "rightType_dashed = TRUE OR leftType_dashed = TRUE",
    "solid": "rightType_solid = TRUE OR leftType_solid = TRUE",
    "dashed_solid": "rightType_dashedsolid = TRUE OR leftType_dashedsolid = TRUE",
    "dashed_dashed": "rightType_dasheddashed = TRUE OR leftType_dasheddashed = TRUE",
    "solid_solid": "rightType_solidsolid = TRUE OR leftType_solidsolid = TRUE",
    "solid_dashed": "rightType_soliddashed = TRUE OR leftType_soliddashed = TRUE",
    "bottsdots": "rightType_botsdots = TRUE OR leftType_botsdots = TRUE",
    "deceleration": "rightType_deceleration = TRUE OR rightType_decelerationsolid = TRUE OR rightType_decelerationdashed = TRUE OR leftType_deceleration = TRUE OR leftType_decelerationsolid = TRUE OR leftType_decelerationdashed = TRUE",
}

LANE_MARK_COLOR_FILTERS = {
    "yellow": "rightColor_yellow = TRUE OR leftColor_yellow = TRUE",
    "white": "rightColor_white = TRUE OR leftColor_white = TRUE",
    "blue": "rightColor_blue = TRUE OR leftColor_blue = TRUE",
}

CURVE_BY_RAD_FILTERS = {
    "dist40_rad100": "curve_rad_ahead < 100",
    "40dist90_rad100": "curve_rad_ahead_40_90 < 100",
    "90dist120_rad100": "curve_rad_ahead_90_120 < 100",
    "120dist_rad100": "curve_rad_ahead_gt_120 < 100",
    "dist40_100rad500": "curve_rad_ahead BETWEEN 100 AND 500",
    "40dist90_100rad500": "curve_rad_ahead_40_90 BETWEEN 100 AND 500",
    "90dist120_100rad500": "curve_rad_ahead_90_120 BETWEEN 100 AND 500",
    "120dist_100rad500": "curve_rad_ahead_gt_120 BETWEEN 100 AND 500",
    "dist40_500rad1000": "curve_rad_ahead BETWEEN 500 AND 1000",
    "40dist90_500rad1000": "curve_rad_ahead_40_90 BETWEEN 500 AND 1000",
    "90dist120_500rad1000": "curve_rad_ahead_90_120 BETWEEN 500 AND 1000",
    "120dist_500rad1000": "curve_rad_ahead_gt_120 BETWEEN 500 AND 1000",
}

CURVE_BY_DIST_FILTERS = {
    "dist40_rad100": "curve_rad_ahead < 100",
    "dist40_100rad500": "curve_rad_ahead BETWEEN 100 AND 500",
    "dist40_500rad1000": "curve_rad_ahead BETWEEN 501 AND 1000",
    "40dist90_rad100": "curve_rad_ahead_40_90 < 100",
    "40dist90_100rad500": "curve_rad_ahead_40_90 BETWEEN 100 AND 500",
    "40dist90_500rad1000": "curve_rad_ahead_40_90 BETWEEN 501 AND 1000",
    "90dist120_rad100": "curve_rad_ahead_90_120 < 100",
    "90dist120_100rad500": "curve_rad_ahead_90_120 BETWEEN 100 AND 500",
    "90dist120_500rad1000": "curve_rad_ahead_90_120 BETWEEN 501 AND 1000",
    "120dist_rad100": "curve_rad_ahead_gt_120 < 100",
    "120dist_100rad500": "curve_rad_ahead_gt_120 BETWEEN 100 AND 500",
    "120dist_500rad1000": "curve_rad_ahead_gt_120 BETWEEN 501 AND 1000",
}

VMAX_BINS = [0, 5, 10, 15, 20, 25, 30, 35]
VMAX_BINS_FILTERS = {}
for i in range(1, len(VMAX_BINS)):
    bin_name = f"vmax_{VMAX_BINS[i - 1]}_{VMAX_BINS[i] - 1}"
    bin_condition = f"vmax_full_range BETWEEN {VMAX_BINS[i - 1]} AND {VMAX_BINS[i] - 1}"
    VMAX_BINS_FILTERS[bin_name] = bin_condition

VMAX_BINS_FILTERS = {
    "vmax_ignore": "vmax_full_range = -1",
    **VMAX_BINS_FILTERS,
    f"vmax_{VMAX_BINS[-1]}_above": f"vmax_full_range >= 35",
}

VMAX_DIST_OPTIONS = [15, 25, 35]
VMAX_DIST_BINS = [0, 50, 100, 200]

dist_from_curve_vmax_filters = []
for option in VMAX_DIST_OPTIONS:
    dist_from_curve_vmax_option_filters = {}
    for i in range(1, len(VMAX_DIST_BINS)):
        bin_name = f"dist_from_curve_vmax_{option}_{VMAX_DIST_BINS[i - 1]}_{VMAX_DIST_BINS[i] - 1}"
        bin_condition = f"dist_from_curve_vmax_{option} BETWEEN {VMAX_DIST_BINS[i - 1]} AND {VMAX_DIST_BINS[i] - 1}"
        dist_from_curve_vmax_option_filters[bin_name] = bin_condition
    dist_from_curve_vmax_filters.append(dist_from_curve_vmax_option_filters)


def get_dist_from_curve_filters(dist, dist_from_curve_vmax_filters):
    return {
        f"dist_from_curve_vmax_{dist}_ignore": f"dist_from_curve_vmax_{dist} = -1",
        **dist_from_curve_vmax_filters,
        f"dist_from_curve_vmax_{dist}_{VMAX_DIST_BINS[-1]}_above": f"dist_from_curve_vmax_{dist} >= {VMAX_DIST_BINS[-1]}",
    }


DIST_FROM_CURVE_VMAX_15_FILTERS = get_dist_from_curve_filters("15", dist_from_curve_vmax_filters[0])
DIST_FROM_CURVE_VMAX_25_FILTERS = get_dist_from_curve_filters("25", dist_from_curve_vmax_filters[1])
DIST_FROM_CURVE_VMAX_35_FILTERS = get_dist_from_curve_filters("35", dist_from_curve_vmax_filters[2])


EVENT_FILTERS = {
    "junction": "dist_to_intersection BETWEEN 0 AND 30",
    "roundabout": "dist_to_roundabout BETWEEN 0 AND 30",
    "hwe_marked": "(dist_to_hwemarked_hostleft BETWEEN 0 AND 40) OR (dist_to_hwemarked_hostright BETWEEN 0 AND 40)",
    "hwe_semimarked": "(dist_to_hwesemimarked_hostleft BETWEEN 0 AND 40) OR (dist_to_hwesemimarked_hostright BETWEEN 0 AND 40)",
    "hwe_unmarked": "(dist_to_hweunmarked_hostleft BETWEEN 0 AND 40) OR (dist_to_hweunmarked_hostright BETWEEN 0 AND 40)",
    "guard_rail_shadows": "shadowsguardrail = TRUE",
    "CA": "dist_to_constarea_true < 40",
}

WEATHER_FILTERS = {
    "rainy_night": "mdbi_time_of_day = 'Night' AND (wetroad = TRUE OR rainy = TRUE OR rain = TRUE)",
    "low_sun": "suninimage = TRUE OR lowsun = TRUE",
}

MAX_SPEED_FILTERS = {"hwe": "dist_to_hwe BETWEEN 0 AND 30", **ROAD_TYPE_FILTERS}

INTERSTING_CAM_HEIGHTS = [0, 1.3, 1.8] + [999]
CAM_HEIGHT_FILTERS = {
    f"{s}_{INTERSTING_CAM_HEIGHTS[i+1]}": f"camh BETWEEN {s} AND {INTERSTING_CAM_HEIGHTS[i+1]}"
    for i, s in enumerate(INTERSTING_CAM_HEIGHTS[:-1])
}

LM_3D_FILTERS = {
    "road_type": ROAD_TYPE_FILTERS,
    "lane_mark_type": LANE_MARK_TYPE_FILTERS,
    "lane_mark_color": LANE_MARK_COLOR_FILTERS,
    "curve_by_dist": CURVE_BY_DIST_FILTERS,
    "event": EVENT_FILTERS,
    "weather": WEATHER_FILTERS,
    "camh": CAM_HEIGHT_FILTERS,
}

PATHNET_MD_FILTERS = {
    "highway": "highway = TRUE OR mdbi_road_highway = TRUE OR mdbi_road_freeway = TRUE",
    "country": "country = TRUE OR mdbi_road_country = TRUE",
    "urban": "urban = TRUE OR mdbi_road_city = TRUE",
    "in_curve": "curve_rad_ahead BETWEEN 0 AND 300",
    "close_curve": "curve_rad_ahead_40_90 BETWEEN 0 AND 250",
    "far_curve": "curve_rad_ahead_150 BETWEEN 0 AND 200",
    "close_merge": "dist_to_merge_rpw BETWEEN 6.5 AND 100",
    "close_split": "dist_to_split_rpw BETWEEN 6.5 AND 66",
    "junction": "dist_to_intersection BETWEEN 0 AND 30",
    "roundabout": "dist_to_roundabout BETWEEN 0 AND 30",
    "CA": "dist_to_constarea_true < 40",
}

PATHNET_MISS_FALSE_FILTERS = {"road_type": PATHNET_ROAD_FILTERS}
LM_3D_INTRESTING_FILTERS = {
    extra_filter_name: f"({extra_filter})"
    for filters_names, filters in LM_3D_FILTERS.items()
    for extra_filter_name, extra_filter in filters.items()
}

ALL_FILTERS = {
    **LANE_MARK_TYPE_FILTERS,
    **LANE_MARK_COLOR_FILTERS,
    **CURVE_BY_DIST_FILTERS,
    **EVENT_FILTERS,
    **WEATHER_FILTERS,
    **MAX_SPEED_FILTERS,
    **LM_3D_INTRESTING_FILTERS,
}
