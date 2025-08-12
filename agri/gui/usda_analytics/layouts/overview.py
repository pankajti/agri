from dash import html, dcc, Input, Output, State, no_update
import dash
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ..components.kpi import kpi_card


def layout():
    return html.Div([
        html.Div([
            kpi_card("kpi-net-sales", "Net Sales (latest wk)"),
            kpi_card("kpi-shipments", "Shipments (latest wk)"),
            kpi_card("kpi-commit-progress", "% of WASDE Exports"),
            kpi_card("kpi-top-buyer", "Top Buyer (YTD)")
        ], className="kpis"),
        html.Div([dcc.Graph(id="g-weekly-trend")], className="card"),
        html.Div([dcc.Graph(id="g-map-destinations")], className="card"),
    ])


def register_callbacks(app):
    @app.callback(
        Output("kpi-net-sales", "children"),
        Output("kpi-shipments", "children"),
        Output("kpi-commit-progress", "children"),
        Output("kpi-top-buyer", "children"),
        Output("g-weekly-trend", "figure"),
        Output("g-map-destinations", "figure"),
        Input("store-exports", "data"),
        Input("store-wasde", "data"),
        Input("store-week-filter", "data"),  # unified window {start, end}
        State("f-countries", "value"),
    )
    def update_overview(exports_data, wasde_data, week_filter, country_filter):
        if not exports_data:
            raise dash.exceptions.PreventUpdate
        df = pd.DataFrame(exports_data)

        # Apply week window from unified store
        if week_filter and week_filter.get("start") and week_filter.get("end"):
            start = pd.to_datetime(week_filter["start"])  # inclusive
            end = pd.to_datetime(week_filter["end"])      # inclusive
            df["week"] = pd.to_datetime(df["week"])  # ensure dtype
            df = df[(df["week"] >= start) & (df["week"] <= end)]

        if df.empty:
            # Gracefully return placeholders
            empty_fig = go.Figure()
            empty_fig.update_layout(margin=dict(l=10, r=10, t=30, b=10))
            return "—", "—", "—", "—", empty_fig, empty_fig

        # Aggregate by week
        df_by_week = df.groupby("week", as_index=False)[["net_sales", "shipments"]].sum().sort_values("week")
        latest_row = df_by_week.iloc[-1]
        net_latest = int(latest_row.get("net_sales", 0))
        ship_latest = int(latest_row.get("shipments", 0))

        # commitments vs WASDE exports
        commitments = int(df_by_week["shipments"].sum())
        wasde = pd.DataFrame(wasde_data or [])
        if not wasde.empty and (wasde["component"] == "Exports").any():
            wasde_exports = float(wasde.loc[wasde["component"] == "Exports", "current"].values[0])
            pct = f"{(commitments / (wasde_exports * 1e6) * 100):.1f}%" if wasde_exports else "—"
        else:
            pct = "—"

        # top buyer within selected window (+ optional filter)
        df_ytd = df
        if country_filter:
            df_ytd = df_ytd[df_ytd["country"].isin(country_filter)]
        top_buyer = df_ytd.groupby("country")["net_sales"].sum().sort_values(ascending=False).head(1)
        top_buyer_str = top_buyer.index[0] if len(top_buyer) else "—"

        # Trend figure within window
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(name="Net Sales", x=df_by_week["week"], y=df_by_week["net_sales"]))
        fig_trend.add_trace(go.Scatter(name="Shipments", x=df_by_week["week"], y=df_by_week["shipments"], mode="lines+markers"))
        fig_trend.update_layout(margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h"))

        # Choropleth by destination (sum over window)
        df_country = df.groupby("country", as_index=False)["net_sales"].sum()
        fig_map = px.choropleth(
            df_country, locations="country", locationmode="country names", color="net_sales",
            title="Net Sales by Destination (Selected Window)"
        )
        fig_map.update_layout(margin=dict(l=0, r=0, t=40, b=0))

        return f"{net_latest:,}", f"{ship_latest:,}", pct, top_buyer_str, fig_trend, fig_map

