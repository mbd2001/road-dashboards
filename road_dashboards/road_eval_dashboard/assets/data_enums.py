from enum import IntEnum


class LMType(IntEnum):
    ignore = -1
    solid = 0
    dashed = 1
    bottsDots = 2

    solidDashed = 3
    dashedSolid = 4
    solidSolid = 5
    dashedDashed = 6

    decelerationSolid = 7
    decelerationDashed = 8


class LMColor(IntEnum):
    yellow = 0
    white = 1
    blue = 2


class LMCaRel(IntEnum):
    ignore = 0
    ca_not_rel = -1
    ca_rel = 1
