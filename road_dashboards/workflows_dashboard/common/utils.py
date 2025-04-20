import plotly.graph_objects as go

BAR_CHART_COLORS = [
    "#1f77b4",  # Blue
    "#ff7f0e",  # Orange
    "#2ca02c",  # Green
    "#d62728",  # Red
    "#9467bd",  # Purple
    "#8c564b",  # Brown
    "#e377c2",  # Pink
    "#7f7f7f",  # Gray
]


def format_workflow_type(workflow_type: str) -> str:
    """Format workflow type for display.

    Args:
        workflow_type: Raw workflow type

    Returns:
        Formatted workflow type
    """
    return " ".join(word.capitalize() for word in workflow_type.split("_"))


def add_center_annotation(fig: go.Figure, text: str) -> None:
    """Add a centered annotation to a pie chart.

    Args:
        fig: Plotly figure
        text: Text to display
    """
    fig.update_layout(
        annotations=[
            dict(
                text=text,
                x=0.5,
                y=0.5,
                font=dict(size=15),
                showarrow=False,
                xanchor="center",
                yanchor="middle",
            )
        ]
    )
