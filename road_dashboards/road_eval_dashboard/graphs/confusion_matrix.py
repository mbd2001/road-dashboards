import numpy as np
import plotly.express as px


def compute_confusion_matrix(data, labels_col, preds_col, num_classes):
    conf_matrix = np.zeros((num_classes, num_classes), dtype=int)

    for ind, row in data.iterrows():
        label_ind = int(max(row[labels_col], 0))
        pred_ind = int(max(row[preds_col], 0))
        conf_matrix[label_ind, pred_ind] = row.res_count
    row_sums = np.array(conf_matrix.sum(axis=1))
    normalize_mat = np.nan_to_num(conf_matrix / row_sums[:, np.newaxis])
    return conf_matrix, normalize_mat


def draw_confusion_matrix(conf_matrix, normalize_mat, class_names, role="", mat_name=""):
    num_classes = len(class_names)
    title = f"{(mat_name or role or 'overall').title()} Confusion Matrix"
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
    return fig


def draw_multiple_nets_confusion_matrix(conf_mats, normalize_mats, net_names, class_names, role="", mat_name=""):
    figs = []
    for ind, net_name in enumerate(net_names):
        fig = draw_confusion_matrix(conf_mats[ind], normalize_mats[ind], class_names, role=role, mat_name=mat_name)
        figs.append(fig)
    return figs
