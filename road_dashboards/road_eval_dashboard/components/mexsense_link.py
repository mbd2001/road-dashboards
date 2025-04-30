from mexsense.mexsense import create_url
from mexsense.models.url_state import BASE, Dataset, DatasetsDescription, Join, Limit, URLState


def get_mexsense_link(suffle_path: str, preds_path: str, query=""):
    datasets = [
        Dataset(
            name=BASE,
            path=suffle_path,
            sql=query,
        ),
        Dataset(
            name="preds",
            path=preds_path,
        ),
    ]
    datasetsDescription = DatasetsDescription(
        datasets=datasets,
        joins=[
            Join(
                name="data",
                datasets=[BASE, "preds"],
                join_on=["clip_name", "grabIndex"],
            )
        ],
    )

    url_state = URLState(
        plugin_id=29,
        limit=Limit.L400,
        vast_data=False,
        selected_partitions={},
        datasets_description=datasetsDescription,
        views_variables=[],
    )
    link = create_url(url_state)
    return link
