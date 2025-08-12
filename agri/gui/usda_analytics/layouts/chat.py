from dash import html, dcc, Input, Output, State


def layout():
    return html.Div([
        html.Div("Ask the analyst (LLM)", className="section-title"),
        html.Div(id="chat-window", className="chat-window"),
        html.Div([
            dcc.Textarea(id="chat-input", style={"width": "100%", "height": 60}),
            html.Button("Ask", id="chat-send"),
        ], className="chat-input")
    ])


def register_callbacks(app):
    @app.callback(
        Output("chat-window", "children"),
        Input("chat-send", "n_clicks"),
        State("chat-input", "value"),
        prevent_initial_call=True,
    )
    def _echo(n, text):
        return html.Div([html.Div(text or "", className="muted")])