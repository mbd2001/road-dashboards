import plotly.express as px


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
