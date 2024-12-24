import json
import os
import re

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pycountry

main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(f"{main_dir}/assets/custom.geo.json") as f:
    geojson = json.load(f)

COUNTRIES_NORMALIZATION: dict[str, str] = {
    "USA": "United States",
    "UAE": "United Arab Emirates",
    "Lichstenstein": "Liechtenstein",
    "Korea": "Korea, Republic of",
    "Bosnia": "Bosnia and Herzegovina",
    "Czech Republic": "Czechia",
    "Uk": "United Kingdom",
    "South Korea": "Korea, Republic of",
    "Russia": "Russian Federation",
}


def generate_world_map(
    countries_data: pd.DataFrame, locations: str, color: str, hover_data: str | list[str] | None = None
) -> go.Figure:
    fig = px.choropleth_mapbox(
        countries_data,
        geojson=geojson,
        locations=locations,
        color=color,
        featureidkey="properties.adm0_a3",
        hover_data=hover_data,
        color_continuous_scale="Blues",
        range_color=(countries_data[color].min(), countries_data[color].max()),
        mapbox_style="carto-positron",
        zoom=1.7,
        center={"lat": 20, "lon": 0},
        opacity=0.5,
    )

    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        coloraxis_colorbar=dict(title="Percentile"),
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="#f8f9fa",
        height=900,
    )
    return fig


def normalize_countries_names(name: str) -> str:
    normalized_name = re.sub("([A-Z]+)", r" \1", name)
    normalized_name = re.sub("  +", " ", normalized_name)
    normalized_name = normalized_name.strip()
    normalized_name = COUNTRIES_NORMALIZATION.get(normalized_name, normalized_name)
    return normalized_name


def iso_alpha_from_name(name: str) -> str:
    iso_alpha = pycountry.countries.get(name=name)
    return iso_alpha.alpha_3 if iso_alpha else "Unknown"


def normalize_countries_count_to_percentiles(data: pd.DataFrame, num_of_percentiles: int = 10) -> np.ndarray:
    N = data.size
    nq = num_of_percentiles
    o = data.argpartition(np.arange(1, nq) * N // nq)
    out = np.empty(N, int)
    out[o] = np.arange(N) * nq // N
    return out
