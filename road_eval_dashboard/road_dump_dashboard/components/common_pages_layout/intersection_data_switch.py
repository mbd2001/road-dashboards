import dash_daq as daq

from road_eval_dashboard.road_dump_dashboard.components.constants.components_ids import INTERSECTION_SWITCH
from road_eval_dashboard.road_dump_dashboard.components.dashboard_layout.layout_wrappers import card_wrapper

layout = card_wrapper(
    daq.BooleanSwitch(
        id=INTERSECTION_SWITCH,
        on=False,
        label="Intersection",
        labelPosition="top",
    ),
)
