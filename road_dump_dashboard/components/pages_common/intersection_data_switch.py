import dash_daq as daq

from road_dump_dashboard.components.components_ids import INTERSECTION_SWITCH
from road_dump_dashboard.components.layout_wrapper import card_wrapper


layout = card_wrapper(
    daq.BooleanSwitch(
        id=INTERSECTION_SWITCH,
        on=False,
        label="Intersection",
        labelPosition="top",
    )
)
