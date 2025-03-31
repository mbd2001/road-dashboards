import dash_bootstrap_components as dbc


def card_wrapper(children):
    return dbc.Card(dbc.CardBody(children), className="mb-4")
