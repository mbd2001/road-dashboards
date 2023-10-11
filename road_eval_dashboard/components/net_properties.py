from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Table:
    paths: List[str]
    required_columns: list
    ignore_filter: str
    ca_ignore_filter: Optional[str] = ""

    def __bool__(self):
        return self.paths is not None


@dataclass
class Nets:
    def __init__(self, net_names, checkpoints, populations, **kwargs):
        self.names = [f"{net_name}_{checkpoint}" for net_name, checkpoint in zip(net_names, checkpoints)]
        self.population = (
            "Test"
            if all("test" in population for population in populations)
            else ("Train" if all("train" in population for population in populations) else "Mix")
        )

        meta_data_tables = kwargs.get("meta_data_table")
        frame_tables = kwargs.get("frame_table")
        pred_tables = kwargs.get("pred_table")
        gt_tables = kwargs.get("pathnet_gt_table")
        dp_tables = kwargs.get("pathnet_pred_table")
        assert meta_data_tables is not None and frame_tables is not None, "missing frame_table and meta_data_table"

        self.meta_data = meta_data_tables[0]
        self.frame_tables = Table(frame_tables, ["clip_name", "grabIndex", "net_id"], "").__dict__
        self.pred_tables = Table(
            pred_tables,
            ["clip_name", "grabIndex", "net_id", "ca_role", "role", "confidence", "ignore", "match", "match_score"],
            "ignore = FALSE",
            "confidence > 0 AND match <> -1 AND ca_role <> 'other'",
        ).__dict__
        self.gt_tables = Table(
            gt_tables,
            ["clip_name", "grabIndex", "net_id", "ca_role", "role", "confidence", "ignore", "match"],
            "ignore = FALSE",
            "confidence > 0 AND match <> -1 AND ca_role <> 'other'",
        ).__dict__
        self.dp_tables = Table(dp_tables, ["clip_name", "grabIndex", "net_id", "role"], "").__dict__
