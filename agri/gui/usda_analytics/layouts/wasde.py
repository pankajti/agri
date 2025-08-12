from dash import html, dcc, Input, Output
import pandas as pd
import plotly.graph_objects as go
from dash.exceptions import PreventUpdate


def layout():
    return html.Div([
        html.Div([dcc.Graph(id="g-balance-bars")], className="card"),
        html.Div([dcc.Graph(id="g-exports-gauge")], className="card"),
    ])


def register_callbacks(app):
    @app.callback(
        Output("g-balance-bars", "figure"),
        Output("g-exports-gauge", "figure"),
        Input("store-wasde", "data"),
        Input("store-exports", "data"),
    )
    def update_wasde(wasde_data, exports_data):
        if not wasde_data or not exports_data:
            raise PreventUpdate  # type: ignore
        bal = pd.DataFrame(wasde_data)

        fig_bal = go.Figure()
        for col in ["current", "prior", "last_year"]:
            fig_bal.add_trace(go.Bar(name=col.replace("_", " ").title(), x=bal["component"], y=bal[col]))
        fig_bal.update_layout(barmode="group", title="WASDE Balance Comparison (Mock)")

        df = pd.DataFrame(exports_data)
        commitments = df.groupby("week")["shipments"].sum().sum()
        wasde_exports = float(bal.loc[bal["component"]=="Exports", "current"].values[0]) * 1e6
        pct = commitments / wasde_exports if wasde_exports else 0

        fig_g = go.Figure(go.Indicator(
            mode="gauge+number",
            value=pct * 100,
            title={'text': "% of WASDE Export Target"},
            gauge={'axis': {'range': [0, 100]}}
        ))

        return fig_bal, fig_g
