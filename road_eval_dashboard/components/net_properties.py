from dataclasses import dataclass
from typing import List


@dataclass
class Net:
    name: str
    checkpoint: str
    population: str
    meta_data_table: str
    frame_table: str
    pred_table: str = ""
    gt_table: str = ""
    dp_table: str = ""


@dataclass
class Nets:
    nets: List[dict]

    def __post_init__(self):
        self.names = [f"{net['name']}_{net['checkpoint']}" for net in self.nets]
        self.meta_data = "" if not self.nets else self.nets[0]["meta_data_table"]
        self.frame_tables = [net["frame_table"] for net in self.nets]
        self.pred_tables = [net["pred_table"] for net in self.nets if net["pred_table"]]
        self.gt_tables = [net["gt_table"] for net in self.nets if net["gt_table"]]
        self.dp_tables = [net["dp_table"] for net in self.nets if net["dp_table"]]
        self.population = (
            "Test"
            if all("test" in net["population"] for net in self.nets)
            else ("Train" if all("train" in net["population"] for net in self.nets) else "Mix")
        )
