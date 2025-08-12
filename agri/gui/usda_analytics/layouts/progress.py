from dash import html, dcc, Input, Output
import pandas as pd
import plotly.express as px
from dash.exceptions import PreventUpdate


def layout():
    return html.Div([
        html.Div([dcc.Graph(id="g-progress-states")], className="card"),
        html.Div([dcc.Graph(id="g-condition-trend")], className="card"),
    ])


def register_callbacks(app):
    @app.callback(
        Output("g-progress-states", "figure"),
        Output("g-condition-trend", "figure"),
        Input("store-progress", "data"),
    )
    def update_progress(progress_data):
        if not progress_data:
            raise PreventUpdate  # type: ignore
        df = pd.DataFrame(progress_data)

        latest = pd.to_datetime(df["week"]).max()
        snap = df[pd.to_datetime(df["week"]) == latest][["state", "planted", "squaring", "setting_bolls"]]
        fig_states = px.bar(snap.melt("state"), x="state", y="value", color="variable", barmode="group",
                            title=f"Crop Stages by State — {latest.date()}")

        cond = df.groupby(pd.to_datetime(df["week"]))["condition_good_excellent"].mean().reset_index(name="condition_good_excellent")
        cond.rename(columns={"week": "week"}, inplace=True)
        fig_cond = px.line(cond, x="week", y="condition_good_excellent", title="Good/Excellent Condition (%)")

        return fig_states, fig_cond