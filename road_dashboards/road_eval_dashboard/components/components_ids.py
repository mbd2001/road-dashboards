# tables names
PATHNET_GT = "pathnet_gt_tables"
PATHNET_PRED = "pathnet_pred_tables"
PATHNET_BOUNDARIES = "pathnet_boundaries_tables"

# stores
NETS = "nets"
GRAPH_TO_COPY = "graph_to_copy"
CATALOG = "catalog"
MD_COLUMNS_TO_TYPE = "md_columns_to_type"
MD_COLUMNS_OPTION = "md_columns_options"
MD_COLUMNS_TO_DISTINCT_VALUES = "md_columns_to_distinct_values"
MD_FILTERS = "md_filters"
PATHNET_FILTERS = "pathnet_filters"
EFFECTIVE_SAMPLES_PER_BATCH = "effective_samples_per_batch"
NET_ID_TO_FB_BEST_THRESH = "net_id_to_fb_best_threshold"
SCENE_SIGNALS_LIST = "scene_signals_list"


# logical components
URL = "url"
PAGE_CONTENT = "page_content"
SIDEBAR = "sidebar"
RUN_EVAL_CATALOG = "run_eval_catalog"
UPDATE_RUNS_BTN = "update_runs_btn"
CLOSEUP_NET = "closeup_net"
LOAD_NETS_DATA_NOTIFICATION = "load_nets_data_notification"
STATE_NOTIFICATION = "state-notification"


# accuracy page
FB_PER_ROAD_TYPE_GRAPH = "fb_per_road_type_graph"
FB_PER_ROAD_TYPE_HOST = "fb_per_road_type_host"

FB_PER_LANE_MARK_TYPE_GRAPH = "fb_per_lane_mark_type_graph"
FB_PER_LANE_MARK_TYPE_HOST = "fb_per_lane_mark_type_host"

FB_PER_LANE_MARK_COLOR_GRAPH = "fb_per_lane_mark_color_graph"
FB_PER_LANE_MARK_COLOR_HOST = "fb_per_lane_mark_color_host"

FB_PER_CURVE_GRAPH = "fb_per_curve_graph"
FB_PER_CURVE_HOST = "fb_per_curve_host"
FB_PER_CURVE_BY_DIST = "fb_per_curve_by_dist"

FB_PER_EVENT_GRAPH = "fb_per_event_graph"
FB_PER_EVENT_HOST = "fb_per_event_host"

FB_PER_WEATHER_GRAPH = "fb_per_weather_graph"
FB_PER_WEATHER_HOST = "fb_per_weather_host"

FB_TRADEOFF_OVERALL = "fb_tradeoff_overall"
FB_TRADEOFF_HOST = "fb_tradeoff_host"

# ca_rel page
CA_REL_OVERALL = "ca_rel_overall"
CA_REL_HOST = "ca_rel_host"
CA_REL_OVERALL_DAY = "ca_rel_overall_day"
CA_REL_OVERALL_NIGHT = "ca_rel_overall_night"

ALL_CA_REL_CONF_MATS = "all_ca_rel_conf_mats"

OVERALL_CA_REL_CONF_MAT = "overall_ca_rel_conf_mat"
HOST_CA_REL_CONF_MAT = "host_ca_rel_conf_mat"

OVERALL_CA_REL_CONF_DIAGONAL = "overall_ca_rel_conf_diagonal"
HOST_CA_REL_CONF_DIAGONAL = "host_ca_rel_conf_diagonal"

# color page
COLOR_OVERALL = "color_overall"
COLOR_HOST = "color_host"
COLOR_OVERALL_DAY = "color_overall_day"
COLOR_OVERALL_NIGHT = "color_overall_night"

ALL_COLOR_CONF_MATS = "all_color_conf_mats"

OVERALL_COLOR_CONF_MAT = "overall_color_conf_mat"
HOST_COLOR_CONF_MAT = "host_color_conf_mat"

OVERALL_COLOR_CONF_DIAGONAL = "overall_color_conf_diagonal"
HOST_COLOR_CONF_DIAGONAL = "host_color_conf_diagonal"


# type page
TYPE_OVERALL = "type_overall"
TYPE_HOST = "type_host"

ALL_TYPE_CONF_MATS = "all_type_conf_mats"

OVERALL_TYPE_CONF_MAT = "overall_type_conf_mat"
HOST_TYPE_CONF_MAT = "host_type_conf_mat"

OVERALL_TYPE_CONF_DIAGONAL = "overall_type_conf_diagonal"
HOST_TYPE_CONF_DIAGONAL = "host_type_conf_diagonal"


# emdp page
EMDP_VIEW_RANGE_HISTOGRAM = "emdp_view_range_histogram"
EMDP_VIEW_RANGE_HISTOGRAM_NAIVE_Z = "emdp_view_range_histogram_naive_z"
EMDP_VIEW_RANGE_HISTOGRAM_CUMULATIVE = "emdp_view_range_histogram_cumulative"
EMDP_VIEW_RANGE_HISTOGRAM_MONOTONIC = "emdp_view_range_histogram_monotonic"
EMDP_VIEW_RANGE_HISTOGRAM_NORM = "emdp_view_range_histogram_norm"
EMDP_VIEW_RANGE_HISTOGRAM_BY_SEC = "emdp_view_range_histogram_by_sec"

EMDP_DP_ERROR_HISTOGRAM = "emdp_dp_error_histogram"

# rem page
REM_SOURCE_DROPDOWN = "rem-source-dropdown"
REM_ACCURACY_ERROR_THRESHOLD_SLIDER = "rem-accuracy-error-threshold-slider"
REM_TABS_CONTENT = "rem-tabs-content"
REM_TABS = "rem-tabs"
REM_AVERAGE_ERROR = "rem_error_histogram"
REM_AVERAGE_ERROR_Z_OR_SEC = "rem_error_histogram_z_or_sec"
REM_ROLES_DROPDOWN = "rem-roles-dropdown"
REM_OVERALL_ACCURATE = "rem-overall-accurate"
REM_IGNORE_COUNT = "rem-ignore-count"

# painted
PAINTED_ROLES_DROPDOWN = "painted-roles-dropdown"
PAINTED_TABS_CONTENT = "painted-tabs-content"
PAINTED_TABS = "painted-tabs"

# width page
WIDTH_ROLES_DROPDOWN = "width-roles-dropdown"
WIDTH_3D_SOURCE_DROPDOWN = "width-3d-source-dropdown"
WIDTH_AVERAGE_ERROR = "width_error_histogram"

# counters
POPULATION_STATE = "population_state"
FRAME_COUNT = "frame_count"
OBJ_COUNT = "obj_count"
EMDP_COUNT = "emdp_count"
DP_COUNT = "dp_count"


# path_net page
PATH_NET_FALSES_HOST = "path_net_losses_host"
PATH_NET_FALSES_NEXT = "path_net_losses_next"

PATH_NET_ACC_ALL_PRED = "path_net_accuracy_all_pred"
PATH_NET_ACC_HOST = "path_net_accuracy_host"
PATH_NET_ACC_NEXT = "path_net_accuracy_next"
PATH_NET_SCENE_ACC_HOST = "path_net_scene_accuracy_host"
PATH_NET_SCENE_ACC_NEXT = "path_net_scene_accuracy_next"
PATH_NET_OOL = "path_net_ool"
PATH_NET_OOL_BORDER_DIST_SLIDER = "path_net_ool_border_dist_slider"
PATH_NET_OOL_RE_DIST_SLIDER = "path_net_ool_re_dist_slider"
PATH_NET_MONOTONE_ACC_HOST = "path_net_monotone_accuracy_host"
PATH_NET_MONOTONE_ACC_NEXT = "path_net_monotone_accuracy_next"
PATH_NET_MISSES_HOST = "path_net_misses_host"
PATH_NET_MISSES_NEXT = "path_net_misses_next"
PATH_NET_QUALITY_TP = "path_net_quality_tp"
PATH_NET_QUALITY_FN = "path_net_quality_fn"
PATH_NET_QUALITY_FP = "path_net_quality_fp"
PATH_NET_QUALITY_TN = "path_net_quality_tn"
PATH_NET_QUALITY_UNMATHCED_CORRECT_REJECTION = "path_net_quality_unmathced_correct_rejection"
PATHNET_BOUNDARY_ACC = "pathnet_boundary_acc"
BOUNDARY_DROP_DOWN = "boundary-dropdown"

PATHNET_MID_PRED_SOURCE = "pathnet_mid_pred_source"
PATHNET_MID_MATCHED_PRED_SOURCE_HOST = "pathnet_mid_matched_pred_source_host"
PATHNET_MID_MATCHED_PRED_SOURCE_NON_HOST = "pathnet_mid_matched_pred_source_non_host"
PATHNET_MID_MATCHED_PRED_SOURCE_ALL = "pathnet_mid_matched_pred_source_all"
PATHNET_MID_MATCHED_INPUT_SOURCE_HOST = "pathnet_mid_matched_input_source_host"
PATHNET_MID_MATCHED_INPUT_SOURCE_NON_HOST = "pathnet_mid_matched_input_source_non_host"
PATHNET_MID_MATCHED_INPUT_SOURCE_ALL = "pathnet_mid_matched_input_source_all"

PATH_NET_CONF_MAT_CARD = "all_conf_mat_id"
PATHNET_TPR_CARD = "all_dp_tpr_card_id"
PATH_NET_ALL_TPR = "all_dp_tpr_id"
PATH_NET_HOST_TPR = "host_dp_tpr_id"
PATH_NET_HOST_CONF_MAT = "host_dp_conf_mat_id"
PATH_NET_ALL_CONF_MATS = "all_dps_conf_mat_id"
PATHNET_INCLUDE_MATCHED_HOST = "pathnet_include_match_host"
PATHNET_INCLUDE_MATCHED_NON_HOST = "pathnet_include_match_non_host"

PATH_NET_BIASES_HOST = "path_net_biases_host"
PATH_NET_BIASES_NEXT = "path_net_biases_next"
PATH_NET_VIEW_RANGES_HOST = "path_net_view_range_host"
PATH_NET_VIEW_RANGES_NEXT = "path_net_view_range_next"

PATHNET_EVENTS_NET_ID_DROPDOWN = "pathnet_events_net_id_dropdown"
PATHNET_EVENTS_CHOSEN_NET = "pathnet_events_chosen_net"
PATHNET_EVENTS_DP_SOURCE_DROPDOWN = "pathnet_events_dp_source_dropdown"
PATHNET_EVENTS_ROLE_DROPDOWN_DIV = "pathnet_events_role_dropdown_div"
PATHNET_EVENTS_ROLE_DROPDOWN = "pathnet_events_role_dropdown"
PATHNET_EVENTS_DIST_DROPDOWN_DIV = "pathnet_events_dist_dropdown_div"
PATHNET_EVENTS_DIST_DROPDOWN = "pathnet_events_dist_dropdown"
PATHNET_EVENTS_EVENTS_ORDER_BY_DIV = "pathnet_events_events_order_by_div"
PATHNET_EVENTS_EVENTS_ORDER_BY = "pathnet_events_events_order_by"
PATHNET_EVENTS_METRIC_DROPDOWN = "pathnet_events_metric_dropdown"
PATHNET_FILTERS_IN_DROPDOWN = "pathnet_filters_in_dropdown"
PATHNET_FILTERS_OUT_DROPDOWN = "pathnet_filters_out_dropdown"
PATHNET_MD_FILTERS_SUBMIT_BUTTON = "pathnet_md_filters_submit_button"
PATHNET_EVENTS_NUM_EVENTS = "pathnet_events_num_events"
PATHNET_EVENTS_NET_CHOOSING_BUTTON = "pathnet_events_net_choosing_button"
PATHNET_EVENTS_SUBMIT_BUTTON = "pathnet_events_submit_button"
PATHNET_EVENTS_DATA_TABLE = "pathnet_events_data_table"
PATHNET_EVENTS_BOOKMARKS_JSON = "pathnet_events_bookmarks_json"
PATHNET_EXPLORER_DATA = "pathnet_explorer_data"
PATHNET_EXTRACT_EVENTS_LOG_MESSAGE = "pathnet_extract_events_log_message"
PATHNET_EXPORT_TO_BOOKMARK_BUTTON = "pathnet_export_to_bookmark_button"
PATHNET_EXPORT_TO_JUMP_BUTTON = "pathnet_export_to_jump_button"
PATHNET_DYNAMIC_DISTANCE_TO_THRESHOLD = "pathnet_dynamic_distance_to_threshold"
PATHNET_DYNAMIC_THRESHOLD_BOUNDARIES = "pathnet_dynamic_threshold_boundaries"
PATHNET_EVENTS_UNIQUE_SWITCH = "pathnet_events_unique_switch"
PATHNET_EVENTS_CLIPS_UNIQUE_SWITCH = "pathnet_events_clips_unique_switch"
PATHNET_EVENTS_REF_DIV = "pathnet_events_ref_div"
PATHNET_EVENTS_REF_NET_ID_DROPDOWN = "pathnet_events_ref_net_id_dropdown"
PATHNET_EVENTS_REF_CHOSEN_NET = "pathnet_events_ref_chosen_net"
PATHNET_EVENTS_REF_DP_SOURCE_DROPDOWN = "pathnet_events_ref_dp_source_dropdown"
PATHNET_EVENTS_EXTRACTOR_DICT = "pathnet_events_extractor_dict"
PATHNET_EVENTS_THRESHOLDS_DIV = "pathnet_events_thresholds_div"
PATHNET_EVENTS_THRESHOLD = "pathnet_events_threshold"
PATHNET_EVENTS_REF_THRESHOLD = "pathnet_events_ref_threshold"
PATHNET_EVENTS_RE_THRESHOLDS_DIV = "pathnet_events_re_thresholds_div"
PATHNET_EVENTS_RE_THRESHOLD = "pathnet_events_re_threshold"
PATHNET_EVENTS_RE_REF_THRESHOLD = "pathnet_events_re_ref_threshold"
PATHNET_EVENTS_RE_SWITCH_DIV = "pathnet_events_re_switch_div"
PATHNET_EVENTS_RE_SWITCH = "pathnet_events_re_switch"

LM_3D_SOURCE_DROPDOWN = "3d-source-dropdown"
LM_3D_ACC_OVERALL = "lm_3d_accuracy_overall"
LM_3D_AVG_ERROR_HOST = "lm_3d_avg_error_host"
LM_3D_AVG_ERROR_NEXT = "lm_3d_avg_error_next"
LM_3D_AVG_ERROR_Z_X = "lm_3d_avg_error_Z_X"
LM_3D_ACC_OVERALL_Z_X = "lm_3d_accuracy_overall_Z_X"
LM_3D_ACC_HOST = "lm_3d_accuracy_host"
LM_3D_ACC_HOST_Z_X = "lm_3d_accuracy_host_Z_X"
LM_3D_ACC_NEXT = "lm_3d_accuracy_next"

# view range page
VIEW_RANGE_SUCCESS_RATE = "view_range_success_rate"
VIEW_RANGE_SUCCESS_RATE_NAIVE_Z = f"{VIEW_RANGE_SUCCESS_RATE}_naive_Z"
VIEW_RANGE_SUCCESS_RATE_ERR_EST = f"{VIEW_RANGE_SUCCESS_RATE}_err_est"
VIEW_RANGE_SUCCESS_RATE_Z_RANGE = f"{VIEW_RANGE_SUCCESS_RATE}_Z_range"
VIEW_RANGE_SUCCESS_RATE_Z_STEP = f"{VIEW_RANGE_SUCCESS_RATE}_Z_step"
VIEW_RANGE_SUCCESS_RATE_ERR_EST_THRESHOLD = f"{VIEW_RANGE_SUCCESS_RATE}_err_est_threshold"

VIEW_RANGE_SUCCESS_RATE_HOST_NEXT = f"{VIEW_RANGE_SUCCESS_RATE}_host_next"
VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_NAIVE_Z = f"{VIEW_RANGE_SUCCESS_RATE_HOST_NEXT}_naive_Z"
VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_ERR_EST = f"{VIEW_RANGE_SUCCESS_RATE_HOST_NEXT}_err_est"
VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_Z_RANGE = f"{VIEW_RANGE_SUCCESS_RATE_HOST_NEXT}_Z_range"
VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_Z_STEP = f"{VIEW_RANGE_SUCCESS_RATE_HOST_NEXT}_Z_step"
VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_ERR_EST_THRESHOLD = f"{VIEW_RANGE_SUCCESS_RATE_HOST_NEXT}_err_est_threshold"

VIEW_RANGE_HISTOGRAM = "view_range_histogram"
VIEW_RANGE_HISTOGRAM_NAIVE_Z = f"{VIEW_RANGE_HISTOGRAM}_naive_Z"
VIEW_RANGE_HISTOGRAM_ERR_EST = f"{VIEW_RANGE_HISTOGRAM}_err_est"
VIEW_RANGE_HISTOGRAM_CUMULATIVE = f"{VIEW_RANGE_HISTOGRAM}_cumulative"
VIEW_RANGE_HISTOGRAM_BIN_SIZE_SLIDER = f"{VIEW_RANGE_HISTOGRAM}_bin_size_slider"
VIEW_RANGE_HISTOGRAM_ERR_EST_THRESHOLD = f"{VIEW_RANGE_HISTOGRAM}_err_est_threshold"

# data exploration page
COUNTRIES_HEAT_MAP = "countries_heat_map"

TVGT_PIE_CHART = "tvgt_pie_chart"
GTEM_PIE_CHART = "gtem_pie_chart"

DYNAMIC_PIE_CHART_DROPDOWN = "dynamic_pie_chart_drop_down"
DYNAMIC_PIE_CHART = "dynamic_pie_chart"
DYNAMIC_PIE_CHART_SLIDER = "dynamic_pie_chart_slider"

ROAD_TYPE_PIE_CHART = "road_type_pie_chart"
LANE_MARK_COLOR_PIE_CHART = "lane_mark_color_pie_chart"

BIN_POPULATION_DROPDOWN = "population_dropdown"
SPLIT_ROLE_POPULATION_DROPDOWN = "split_role_population_dropdown"
ROLE_POPULATION_VALUE = "role_population_value"
# scene page
ALL_SCENE_SCORES = "all_scene_scores"
SCENE_SCORE = "scene_score"
ALL_SCENE_CONF_MATS = "all_scene_conf_mats"
SCENE_CONF_MAT = "scene_conf_mat"
ALL_SCENE_CONF_DIAGONALS = "all_scene_conf_diagonals"
SCENE_CONF_DIAGONALS = "scene_conf_diagonals"
ALL_SCENE_CONF_MATS_MEST = "all_scene_conf_mats_MEST"
SCENE_CONF_MAT_MEST = "scene_conf_mat_MEST"
ALL_SCENE_CONF_DIAGONALS_MEST = "all_scene_conf_diagonals_MEST"
SCENE_CONF_DIAGONALS_MEST = "scene_conf_diagonals_MEST"
ALL_SCENE_ROC_CURVES = "all_scene_ROC_curves"
SCENE_ROC_CURVE = "scene_ROC_curve"
SCENE_SIGNALS_CONF_MATS_DATA = "scene_signals_conf_mats_data"
SCENE_SIGNALS_DATA_READY = "scene_signals_data_ready"
