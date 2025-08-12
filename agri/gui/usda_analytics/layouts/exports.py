from dash import html, dcc, Input, Output
import dash
import pandas as pd
import plotly.express as px
from dash import dash_table


def layout():
    return html.Div([
        html.Div([dcc.Graph(id="g-top-buyers")], className="card"),
        html.Div([
            dash_table.DataTable(
                id="tbl-exports",
                columns=[
                    {"name": "Week", "id": "week"},
                    {"name": "Country", "id": "country"},
                    {"name": "Net Sales", "id": "net_sales", "type": "numeric", "format": dict(specifier=",")},
                    {"name": "Shipments", "id": "shipments", "type": "numeric", "format": dict(specifier=",")},
                ],
                page_size=12,
                style_table={"overflowX": "auto"},
            )
        ], className="card"),
    ])


def register_callbacks(app):
    @app.callback(
        Output("g-top-buyers", "figure"),
        Output("tbl-exports", "data"),
        Input("store-exports", "data"),
        Input("store-week-filter", "data"),
        Input("f-countries", "value"),
    )
    def update_exports(exports_data, week_filter, country_filter):
        if not exports_data:
            raise dash.exceptions.PreventUpdate
        df = pd.DataFrame(exports_data)
        df["week"] = pd.to_datetime(df["week"])  # ensure dtype

        # apply unified week window
        if week_filter and week_filter.get("start") and week_filter.get("end"):
            start = pd.to_datetime(week_filter["start"])
            end = pd.to_datetime(week_filter["end"])
            df = df[(df["week"] >= start) & (df["week"] <= end)]

        if country_filter:
            df = df[df["country"].isin(country_filter)]

        if df.empty:
            return px.bar(pd.DataFrame(columns=["country", "net_sales"]), x="country", y="net_sales", title="Top Buyers (Selected Window)"), []

        buyers = (
            df.groupby("country", as_index=False)[["net_sales", "shipments"]]
              .sum()
              .sort_values("net_sales", ascending=False)
              .head(10)
        )
        fig = px.bar(buyers, x="country", y="net_sales", title="Top Buyers (Selected Window)")

        # table for the selected window (last 12 distinct weeks *within* window)
        latest_weeks = df["week"].drop_duplicates().sort_values().tail(12)
        tbl_df = df[df["week"].isin(latest_weeks)].sort_values(["week", "country"]).copy()
        tbl_df.loc[:, "week"] = pd.to_datetime(tbl_df["week"]).dt.date.astype(str)

        return fig, tbl_df.to_dict("records")