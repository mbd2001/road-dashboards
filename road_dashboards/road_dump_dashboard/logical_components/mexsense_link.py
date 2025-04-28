from mexsense.mexsense import create_url
from mexsense.models.url_state import BASE, Dataset, DatasetsDescription, Limit, URLState


def get_mexsense_link(suffle_path: str, query=""):
    datasets = [
        Dataset(
            name=BASE,
            path=suffle_path,
            sql=query,
        ),
    ]
    datasetsDescription = DatasetsDescription(
        datasets=datasets,
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
