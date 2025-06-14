import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def compute_confusion_matrix(
    data: pd.DataFrame, main_val: str, secondary_val: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    conf_matrix = data.pivot_table(index=main_val, columns=secondary_val, values="overall", aggfunc="sum")
    row_sums = np.array(conf_matrix.sum(axis=1))
    normalize_mat = np.nan_to_num(conf_matrix / row_sums[:, np.newaxis])
    return conf_matrix, normalize_mat


def draw_confusion_matrix(
    conf_matrix: pd.DataFrame, normalize_mat: pd.DataFrame, x_label: str = "", y_label: str = "", title: str = ""
) -> go.Figure:
    num_classes = max(len(conf_matrix.index), len(conf_matrix.columns))
    fig = px.imshow(
        normalize_mat,
        text_auto=".2f",
        title=title,
        x=conf_matrix.columns,
        y=conf_matrix.index,
        color_continuous_scale="blues",
        labels={"x": x_label, "y": y_label},
    )
    fig.update(
        data=[
            {
                "customdata": conf_matrix,
                "hovertemplate": "label: %{y}<br>pred: %{x}<br>percentage: %{z}<br>frames: %{customdata}",
            }
        ],
        layout_coloraxis_showscale=False,
    )
    fig.update_layout(height=max(500, 90 * num_classes))
    return fig


def get_confusion_matrix(
    data: pd.DataFrame, main_val: str, secondary_val: str, x_label: str = "", y_label: str = "", title: str = ""
) -> go.Figure:
    conf_matrix, normalize_mat = compute_confusion_matrix(data, main_val, secondary_val)
    fig = draw_confusion_matrix(conf_matrix, normalize_mat, x_label=x_label, y_label=y_label, title=title)
    return fig
