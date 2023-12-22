import plotly.express as px
import numpy as np
import pandas as pd


def compute_confusion_matrix(data, labels_col, preds_col, num_classes):
    conf_matrix = pd.DataFrame(np.zeros((num_classes, num_classes), dtype=int))

    for ind, row in data.iterrows():
        label_ind = max(row[labels_col], 0)
        pred_ind = max(row[preds_col], 0)
        conf_matrix.loc[label_ind, pred_ind] = row.res_count
    row_sums = np.array(conf_matrix.sum(axis=1))
    normalize_mat = (conf_matrix / row_sums[:, np.newaxis]).fillna(0)
    return conf_matrix, normalize_mat


def draw_confusion_matrix(data, labels_col, preds_col, class_names, role="", mat_name=""):
    num_classes = len(class_names)
    conf_matrix, normalize_mat = compute_confusion_matrix(data, labels_col, preds_col, num_classes)
    title = f'{(mat_name or role or "overall").title()} Confusion Matrix'
    fig = px.imshow(
        normalize_mat,
        text_auto=".2f",
        title=title,
        x=class_names,
        y=class_names,
        color_continuous_scale="blues",
        labels={"x": "Predictions", "y": "Labels"},
    )
    fig.update(
        data=[
            {
                "customdata": conf_matrix,
                "hovertemplate": "label: %{y}<br>pred: %{x}<br>percentage: %{z}<br>lane marks: %{customdata}",
            }
        ],
        layout_coloraxis_showscale=False,
    )
    fig.update_layout(height=max(500, 90 * num_classes))
    return fig, normalize_mat


def draw_multiple_nets_confusion_matrix(data, labels_col, preds_col, net_names, class_names, role="", mat_name=""):
    figs = []
    normalize_mats = []
    for net_name in net_names:
        net_data = data[data["net_id"] == net_name]
        fig, normalize_mat = draw_confusion_matrix(
            net_data, labels_col, preds_col, class_names, role=role, mat_name=mat_name
        )
        figs.append(fig)
        normalize_mats.append(normalize_mat)
    return figs, normalize_mats
