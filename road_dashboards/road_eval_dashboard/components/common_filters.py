ROAD_TYPE_FILTERS = {
    "highway": "mdbi_road_highway = TRUE OR mdbi_road_freeway = TRUE",
    "country": "mdbi_road_country = TRUE",
    "urban": "mdbi_road_city = TRUE",
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
    f"vmax_{VMAX_BINS[-1]}_above": "vmax_full_range >= 35",
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
    f"{s}_{INTERSTING_CAM_HEIGHTS[i + 1]}": f"camh BETWEEN {s} AND {INTERSTING_CAM_HEIGHTS[i + 1]}"
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
    "highway": "(highway = TRUE OR freeway = TRUE)",
    "country": "country = TRUE",
    "urban": "urban = TRUE",
    "in_curve": "curve_rad_ahead BETWEEN 0 AND 300",
    "close_curve": "curve_rad_ahead_40_90 BETWEEN 0 AND 250",
    "far_curve": "curve_rad_ahead_150 BETWEEN 0 AND 200",
    "ramp": "ramp = TRUE AND curve_rad_ahead_40_90 < 800",
    "close_merge": "dist_to_merge_rpw BETWEEN 6.5 AND 80",
    "far_merge": "dist_to_merge_rpw BETWEEN 80 AND 150",
    "close_split": "dist_to_split_rpw BETWEEN 6.5 AND 80",
    "far_split": "dist_to_split_rpw BETWEEN 80 AND 150",
    "junction": "dist_to_intersection BETWEEN 0 AND 50 AND dist_to_cipv_rpw > 10",
    "roundabout": "dist_to_roundabout BETWEEN 0 AND 30 AND dist_to_cipv_rpw > 10",
    "CA": "(CAST(is_rem_rpw AS BOOLEAN) or urban) = FALSE AND (dist_to_constarea_true BETWEEN 0 AND 60) AND (dist_to_cipv_rpw > 10)",
}

COMMON_FILTERS = {
    "is_rem": "CAST(is_rem_rpw AS BOOLEAN) = TRUE",
    "is_not_rem": "CAST(is_rem_rpw AS BOOLEAN) = FALSE",
    "is_tvfix": "is_tvfix_rpw = TRUE",
    "is_dp_perf": "is_tvgt_rpw = TRUE",
    "CA": "(dist_to_constarea_true BETWEEN 0 AND 60)",
    "no_CA": "(dist_to_constarea_true BETWEEN 0 AND 60) = FALSE",
    "far_from_cipv": "dist_to_cipv_rpw > 10",
    "no_slow_speed": "speed > 5.555",
    "no_lane_change": "dist_to_host_at_z0_rpw < 0.75 AND CAST(valid_roles_rpw AS BOOLEAN) = TRUE",
    "CA_to_from_close": "((dist_to_constarea_true BETWEEN 0.1 AND 20) OR (dist_from_constarea_true BETWEEN 0.1 AND 20))",
    "close_to_cipv": "dist_to_cipv_rpw <= 10",
    "urban": PATHNET_MD_FILTERS["urban"],
    "no_intersection": "dist_to_intersection > 150",
    "yellow": "(rightColor_yellow = TRUE OR leftColor_yellow = TRUE)",
    "lane_change": "(dist_to_host_at_z0_rpw > 0.75 OR CAST(valid_roles_rpw AS BOOLEAN) = FALSE)",
    "slow_speed": "speed <= 5.555",
}

POPULAR_IGNORES = {
    "no_cipv_ca": f"({COMMON_FILTERS['no_CA']} AND {COMMON_FILTERS['far_from_cipv']})",
    "no_cipv_slow_ca": f"({COMMON_FILTERS['no_CA']} AND {COMMON_FILTERS['far_from_cipv']} AND {COMMON_FILTERS['no_slow_speed']})",
    "no_cipv_slow_ca_lc": f"({COMMON_FILTERS['no_CA']} AND {COMMON_FILTERS['far_from_cipv']} AND {COMMON_FILTERS['no_slow_speed']} AND {COMMON_FILTERS['no_lane_change']})",
    "no_cipv": f"{COMMON_FILTERS['far_from_cipv']}",
    "no_slow_speed": f"{COMMON_FILTERS['no_slow_speed']}",
    "no_split_merge": "num_dp_splits_rpw = 0 AND num_dp_merges_rpw = 0",
    "no_rem_or_urban": f"({COMMON_FILTERS['is_not_rem']} AND urban = FALSE)",
    "not_urban": "urban = FALSE",
    "not_all_host_turn_junc": "CAST(all_hosts_turn_in_junction_rpw AS BOOLEAN) = FALSE",
    "no_in_junction_turning": "CAST(in_junction_turning_rpw AS BOOLEAN) = FALSE",
    "no_junc_curve": "host_junc_delta_heading_rpw < 5 AND host_junc_delta_x_rpw < 1.5",
}


JUNCTION_SCENE_FILTERS = {
    "large_junction_no_curve": f"(dist_to_intersection BETWEEN 3 AND 50) AND (next_junction_length_rpw BETWEEN 20 AND 70) AND {POPULAR_IGNORES['no_junc_curve']} AND {POPULAR_IGNORES['not_all_host_turn_junc']} AND {POPULAR_IGNORES['no_cipv_ca']}",
    "small_junction_no_curve": f"(dist_to_intersection BETWEEN 3 AND 50) AND (next_junction_length_rpw BETWEEN 1 AND 20) AND {POPULAR_IGNORES['no_junc_curve']} AND {POPULAR_IGNORES['not_all_host_turn_junc']} AND {POPULAR_IGNORES['no_cipv_ca']}",
    "curve_junction": f"(dist_to_intersection BETWEEN 3 AND 50) AND host_junc_delta_heading_rpw > 7 AND {POPULAR_IGNORES['no_cipv_ca']} AND {POPULAR_IGNORES['not_all_host_turn_junc']}",
    "shift_junction": f"(dist_to_intersection BETWEEN 3 AND 50) AND (host_junc_delta_heading_rpw BETWEEN 0 AND 2) AND (host_junc_delta_x_rpw BETWEEN 1.5 AND 6) AND {POPULAR_IGNORES['no_cipv_ca']}",
    "in_junction_no_curve": f"dist_to_intersection BETWEEN 0 AND 3 AND {POPULAR_IGNORES['no_cipv_ca']} AND {POPULAR_IGNORES['no_in_junction_turning']} AND {POPULAR_IGNORES['no_junc_curve']}",
    "in_junction_curve": f"dist_to_intersection BETWEEN 0 AND 3 AND host_junc_delta_heading_rpw > 7 AND {POPULAR_IGNORES['no_cipv_ca']} AND {POPULAR_IGNORES['no_in_junction_turning']}",
    "in_junction_shift_curve": f"dist_to_intersection BETWEEN 0 AND 3 AND (host_junc_delta_heading_rpw BETWEEN 0 AND 2) AND (host_junc_delta_x_rpw BETWEEN 1.5 AND 6) AND {POPULAR_IGNORES['no_cipv_ca']} AND {POPULAR_IGNORES['no_in_junction_turning']}",
    "junction_no_curve_no_urban": f"dist_to_intersection BETWEEN 3 AND 50 AND urban = FALSE AND {POPULAR_IGNORES['no_junc_curve']} AND {POPULAR_IGNORES['not_all_host_turn_junc']} AND {POPULAR_IGNORES['no_cipv_ca']}",
    "curve_junction_no_urban": f"(dist_to_intersection BETWEEN 3 AND 50) AND urban = FALSE AND host_junc_delta_heading_rpw > 7 AND {POPULAR_IGNORES['no_cipv_ca']} AND {POPULAR_IGNORES['not_all_host_turn_junc']}",
    "shift_junction_no_urban": f"(dist_to_intersection BETWEEN 3 AND 50) AND urban = FALSE AND (host_junc_delta_heading_rpw BETWEEN 0 AND 2) AND (host_junc_delta_x_rpw BETWEEN 1.5 AND 6) AND {POPULAR_IGNORES['no_cipv_ca']}",
    "in_junction_no_urban": f"(dist_to_intersection BETWEEN 0 AND 3) AND urban = FALSE AND {POPULAR_IGNORES['no_in_junction_turning']} AND {POPULAR_IGNORES['no_cipv_ca']}",
}


CA_SCENE_FILTERS = {
    "CA_yellow": f"{COMMON_FILTERS['CA']} AND {COMMON_FILTERS['yellow']} AND {POPULAR_IGNORES['no_rem_or_urban']} AND {POPULAR_IGNORES['no_cipv']}",
    "CA_crossing": f"({COMMON_FILTERS['CA_to_from_close']} OR dist_to_cacrossing < 80) AND {POPULAR_IGNORES['no_rem_or_urban']} AND {POPULAR_IGNORES['no_cipv']}",
    "CA": f"{COMMON_FILTERS['CA']} AND {POPULAR_IGNORES['no_rem_or_urban']} AND {POPULAR_IGNORES['no_cipv']}",
}


CURVES_SCENE_FILTERS = {
    "strong_mid_hilly_curve_rem": f"(curve_rad_ahead_150 BETWEEN 0 AND 500) AND ({POPULAR_IGNORES['no_split_merge']} AND {COMMON_FILTERS['is_rem']} AND {POPULAR_IGNORES['no_cipv_slow_ca']} AND vertical_change_50m_rpw > 1)",
    "strong_curve_rem": f"(curve_rad_ahead_150 BETWEEN 0 AND 250) AND ({POPULAR_IGNORES['no_split_merge']} AND {COMMON_FILTERS['is_rem']} AND {POPULAR_IGNORES['no_cipv_slow_ca']})",
    "mid_curve_rem": f"(curve_rad_ahead_150 BETWEEN 250 AND 500) AND ({POPULAR_IGNORES['no_split_merge']} AND {COMMON_FILTERS['is_rem']} AND {POPULAR_IGNORES['no_cipv_slow_ca']})",
    "weak_curve_rem": f"(curve_rad_ahead_150 BETWEEN 500 AND 800) AND ({POPULAR_IGNORES['no_split_merge']} AND {COMMON_FILTERS['is_rem']} AND {POPULAR_IGNORES['no_cipv_slow_ca']})",
    "strong_mid_hilly_curve_tv": f"(curve_rad_ahead_150 BETWEEN 0 AND 500) AND ({POPULAR_IGNORES['no_split_merge']} AND {COMMON_FILTERS['is_not_rem']} AND {POPULAR_IGNORES['no_cipv_slow_ca']} AND vertical_change_50m_rpw > 1)",
    "strong_curve_tv": f"(curve_rad_ahead_150 BETWEEN 0 AND 250) AND ({POPULAR_IGNORES['no_split_merge']} AND {COMMON_FILTERS['is_not_rem']} AND {POPULAR_IGNORES['no_cipv_slow_ca']})",
    "mid_curve_tv": f"(curve_rad_ahead_150 BETWEEN 250 AND 500) AND ({POPULAR_IGNORES['no_split_merge']} AND {COMMON_FILTERS['is_not_rem']} AND {POPULAR_IGNORES['no_cipv_slow_ca']})",
    "weak_curve_tv": f"(curve_rad_ahead_150 BETWEEN 500 AND 800) AND ({POPULAR_IGNORES['no_split_merge']} AND {COMMON_FILTERS['is_not_rem']} AND {POPULAR_IGNORES['no_cipv_slow_ca']})",
    "ramp": f"({PATHNET_MD_FILTERS['ramp']} AND {POPULAR_IGNORES['no_split_merge']} AND {POPULAR_IGNORES['no_cipv_slow_ca']})",
}

HWE_SCENE_FILTERS = {
    "marked": "((dist_to_hwemarked_hostleft BETWEEN 0 AND 40) OR (dist_to_hwemarked_hostright BETWEEN 0 AND 40)) AND urban = FALSE",
    "semi_marked": "((dist_to_hwesemimarked_hostleft BETWEEN 0 AND 40) OR (dist_to_hwesemimarked_hostright BETWEEN 0 AND 40)) AND urban = FALSE",
    "unmarked": "((dist_to_hweunmarked_hostleft BETWEEN 0 AND 40) OR (dist_to_hweunmarked_hostright BETWEEN 0 AND 40)) AND urban = FALSE",
    "merge": "(dist_to_lanemerge BETWEEN 0 AND 50) AND urban = FALSE",
}


PATHNET_ROAD_FILTERS = {
    "highway": PATHNET_MD_FILTERS["highway"],
    "country": PATHNET_MD_FILTERS["country"],
    "urban": PATHNET_MD_FILTERS["urban"],
    "other": "(highway OR country OR urban OR freeway) = FALSE",
    "all": "(urban = TRUE or urban = FALSE)",
}

PATHNET_MISS_FALSE_FILTERS = {"road_type": PATHNET_ROAD_FILTERS}
PATHNET_BATCH_BY_SEC_FILTERS = {
    "Curve": CURVES_SCENE_FILTERS,
    "Junction": JUNCTION_SCENE_FILTERS,
    "CA": CA_SCENE_FILTERS,
    "HWE": HWE_SCENE_FILTERS,
}
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
