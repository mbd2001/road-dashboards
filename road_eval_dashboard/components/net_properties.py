from dataclasses import dataclass
from typing import List, Optional

from road_eval_dashboard.components.queries_manager import ZSources, lm_3d_distances


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
    def __init__(self, net_names, checkpoints, use_cases, populations, **kwargs):
        self.names = [
            f"{net_name}_{checkpoint}_{use_case}"
            for net_name, checkpoint, use_case in zip(net_names, checkpoints, use_cases)
        ]
        self.population = (
            "Test"
            if all("test" in population for population in populations)
            else ("Train" if all("train" in population for population in populations) else "Mix")
        )

        meta_data_tables = kwargs.get("meta_data_table")
        frame_tables = kwargs.get("frame_table")
        pred_tables = kwargs.get("pred_table")
        gt_tables = kwargs.get("gt_table")
        pathnet_pred_tables = kwargs.get("pathnet_pred_table")
        pathnet_gt_tables = kwargs.get("pathnet_gt_table")
        pathnet_host_boundaries = kwargs.get("boundries_df_table")
        assert meta_data_tables is not None and frame_tables is not None, "missing frame_table and meta_data_table"

        self.meta_data = meta_data_tables[0]
        self.frame_tables = Table(frame_tables, ["clip_name", "grabIndex", "net_id"], "").__dict__
        self.pred_tables = Table(
            pred_tables,
            ["clip_name", "grabIndex", "net_id", "ca_role", "role", "confidence", "ignore", "match", "match_score"],
            "ignore = FALSE",
            "confidence > 0 AND match <> -1 AND ca_role <> 'other'",
        )
        self.gt_tables = Table(
            gt_tables,
            ["clip_name", "grabIndex", "net_id", "ca_role", "role", "confidence", "ignore", "match"]
            + [
                f'"pos_dZ_{source}_{axis}_dists_{sec}"'
                for sec in lm_3d_distances
                for axis in ["Z", "X"]
                for source in [s.value for s in ZSources]
            ],
            "ignore = FALSE",
            "confidence > 0 AND match <> -1 AND ca_role <> 'other'",
        )
        pathnet_columns = [
            "clip_name",
            "grabIndex",
            "net_id",
            "role",
            "bin_population",
            "smooth_index",
        ] + [f'"dist_{dist / 2}"' for dist in range(1, 11)]
        bounadaries_columns = ["clip_name", "grabIndex", "net_id"] + [
            f'"{dist}_{side}"' for dist in ["dist_0.5", "dist_1.3", "dist_2.0"] for side in ["left", "right"]
        ]
        self.pathnet_pred_tables = Table(pathnet_pred_tables, pathnet_columns, "")
        self.pathnet_gt_tables = Table(pathnet_gt_tables, pathnet_columns, "")
        self.pathnet_host_boundaries = Table(pathnet_host_boundaries, bounadaries_columns, "")
        self.pred_tables = self.pred_tables.__dict__ if self.pred_tables else None
        self.gt_tables = self.gt_tables.__dict__ if self.gt_tables else None
        self.pathnet_pred_tables = self.pathnet_pred_tables.__dict__ if self.pathnet_pred_tables else None
        self.pathnet_gt_tables = self.pathnet_gt_tables.__dict__ if self.pathnet_gt_tables else None
        self.pathnet_host_boundaries = self.pathnet_host_boundaries.__dict__ if self.pathnet_host_boundaries else None
