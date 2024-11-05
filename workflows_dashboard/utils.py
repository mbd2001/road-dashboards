import plotly.express as px


def format_workflow_name(workflow_name: str) -> str:
    """Format workflow name for display.

    Handles both single and multi-word workflow names:
    - Single word: 'gtrm_workflow' -> 'GTRM Workflow'
    - Multi-word: 'drone_view_workflow' -> 'Drone View Workflow'
    """
    prefix = workflow_name.replace("_workflow", "")
    words = prefix.split("_")

    if len(words) == 1:
        formatted = prefix.upper()
    else:
        formatted = " ".join(word.title() for word in words)

    return f"{formatted} Workflow"


def add_center_annotation(fig: px.pie, text: str) -> None:
    """Add a consistently styled center annotation to a plotly figure."""
    fig.add_annotation(
        text=text,
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=12, color="black"),
        xanchor="center",
        yanchor="middle",
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="rgba(0, 0, 0, 0.3)",
        borderwidth=1,
    )


def create_empty_chart() -> px.pie:
    fig = px.pie(values=[], names=[], title="No data to display")
    return fig
