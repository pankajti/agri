from dash import html

def kpi_card(id_, title, value="—"):
    return html.Div([
        html.Div(title, className="kpi-title"),
        html.Div(id=id_, className="kpi-value", children=value)
    ], className="kpi")