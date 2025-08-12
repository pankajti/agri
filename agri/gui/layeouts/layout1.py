import dash
from dash import Dash, dcc, html, Input, Output, State, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import date, timedelta

# -------------------------------------------------
# Mock loaders (replace with real USDA loaders)
# -------------------------------------------------

def load_weekly_exports(commodity="Cotton", weeks=52):
    """Return mock weekly export sales by destination."""
    np.random.seed(0)
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=weeks, freq="W-THU")
    countries = ["China", "Vietnam", "Pakistan", "Bangladesh", "Turkey", "Indonesia", "Mexico", "Thailand", "India", "Others"]
    df = pd.DataFrame({
        "week": np.repeat(dates, len(countries)),
        "country": countries * len(dates),
        "net_sales": np.random.randint(0, 200, size=len(dates) * len(countries)) * 100,
        "shipments": np.random.randint(0, 250, size=len(dates) * len(countries)) * 100,
        "commodity": commodity,
        "my": "2024/25",
    })
    return df


def load_wasde_balance(commodity="Cotton"):
    comps = ["Beginning Stocks", "Production", "Imports", "Total Supply", "Domestic Use", "Exports", "Ending Stocks"]
    vals = [4.3, 15.0, 0.5, 19.8, 2.5, 12.8, 4.5]  # mock
    prior = [4.2, 14.8, 0.5, 19.5, 2.6, 12.6, 4.3]
    last_year = [3.8, 14.2, 0.6, 18.6, 2.4, 12.2, 4.0]
    return pd.DataFrame({"component": comps, "current": vals, "prior": prior, "last_year": last_year, "commodity": commodity})


def load_crop_progress(commodity="Cotton"):
    states = ["TX", "GA", "MS", "AR", "NC", "AZ", "CA", "LA", "MO", "OK"]
    weeks = pd.date_range("2025-04-01", periods=20, freq="W-MON")
    df = []
    for st in states:
        for w in weeks:
            df.append({
                "state": st,
                "week": w,
                "planted": np.clip(np.random.normal(80, 15), 0, 100),
                "squaring": np.clip(np.random.normal(50, 20), 0, 100),
                "setting_bolls": np.clip(np.random.normal(30, 20), 0, 100),
                "condition_good_excellent": np.clip(np.random.normal(55, 10), 0, 100),
            })
    return pd.DataFrame(df)


# -------------------------------------------------
# App init
# -------------------------------------------------
app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# Global stores (can swap to Redis/Flask-Caching in prod)
app.layout = html.Div([
    # Top Bar
    html.Div([
        html.Div("USDA Agri Analytics", className="title"),
        html.Div(id="last-updated", className="muted")
    ], className="topbar"),

    # Body
    html.Div([
        # Sidebar
        html.Div([
            html.Label("Commodity"),
            dcc.Dropdown(id="f-commodity", options=["Cotton", "Wheat", "Corn", "Soybeans"], value="Cotton", clearable=False),

            html.Label("Marketing Year"),
            dcc.Dropdown(id="f-my", options=["2024/25", "2023/24", "2022/23"], value="2024/25", clearable=False),

            html.Label("Destinations"),
            dcc.Dropdown(id="f-countries", multi=True),

            html.Label("Week Range"),
            dcc.RangeSlider(id="f-weeks", min=1, max=52, step=1, value=[40, 52], tooltip={"placement": "bottom"}),

            html.Hr(),
            html.Button("Refresh Data", id="btn-refresh"),
            html.Div(id="refresh-note", className="muted"),

            html.Hr(),
            html.Div("Data Catalog"),
            html.Ul([
                html.Li("FAS Weekly Export Sales"),
                html.Li("NASS Crop Progress & Condition"),
                html.Li("WASDE Balance Sheets"),
                html.Li("Grain Inspections (AMS/FAS)"),
            ], className="muted")
        ], className="sidebar"),

        # Main Content
        html.Div([
            dcc.Tabs(id="tabs", value="tab-overview", children=[
                dcc.Tab(label="Overview", value="tab-overview"),
                dcc.Tab(label="Weekly Exports", value="tab-exports"),
                dcc.Tab(label="Crop Progress", value="tab-progress"),
                dcc.Tab(label="WASDE Balance", value="tab-wasde"),
                dcc.Tab(label="Analyst Chat", value="tab-chat"),
            ]),
            html.Div(id="tab-content", className="content")
        ], className="main")
    ], className="container"),

    # Stores
    dcc.Store(id="store-exports"),
    dcc.Store(id="store-wasde"),
    dcc.Store(id="store-progress"),
], className="app")


# -------------------------------------------------
# Page factories
# -------------------------------------------------

def kpi_card(id_, title, value="—"):
    return html.Div([
        html.Div(title, className="kpi-title"),
        html.Div(id=id_, className="kpi-value", children=value)
    ], className="kpi")


def layout_overview():
    return html.Div([
        html.Div([
            kpi_card("kpi-net-sales", "Net Sales (latest wk)"),
            kpi_card("kpi-shipments", "Shipments (latest wk)"),
            kpi_card("kpi-commit-progress", "% of WASDE Exports"),
            kpi_card("kpi-top-buyer", "Top Buyer (YTD)")
        ], className="kpis"),

        html.Div([
            dcc.Graph(id="g-weekly-trend"),
        ], className="card"),

        html.Div([
            dcc.Graph(id="g-map-destinations"),
        ], className="card")
    ])


def layout_exports():
    return html.Div([
        html.Div([
            dcc.Graph(id="g-top-buyers"),
        ], className="card"),

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
        ], className="card")
    ])


def layout_progress():
    return html.Div([
        html.Div([
            dcc.Graph(id="g-progress-states"),
        ], className="card"),
        html.Div([
            dcc.Graph(id="g-condition-trend"),
        ], className="card")
    ])


def layout_wasde():
    return html.Div([
        html.Div([
            dcc.Graph(id="g-balance-bars"),
        ], className="card"),
        html.Div([
            dcc.Graph(id="g-exports-gauge"),
        ], className="card")
    ])


def layout_chat():
    return html.Div([
        html.Div("Ask the analyst (LLM)", className="section-title"),
        html.Div(id="chat-window", className="chat-window"),
        html.Div([
            dcc.Textarea(id="chat-input", style={"width": "100%", "height": 60}),
            html.Button("Ask", id="chat-send"),
        ], className="chat-input")
    ])


# -------------------------------------------------
# Routing
# -------------------------------------------------
@app.callback(Output("tab-content", "children"), Input("tabs", "value"))
def render_tab(tab):
    if tab == "tab-overview":
        return layout_overview()
    if tab == "tab-exports":
        return layout_exports()
    if tab == "tab-progress":
        return layout_progress()
    if tab == "tab-wasde":
        return layout_wasde()
    if tab == "tab-chat":
        return layout_chat()
    return html.Div()


# -------------------------------------------------
# Data refresh + options
# -------------------------------------------------
@app.callback(
    Output("store-exports", "data"),
    Output("store-wasde", "data"),
    Output("store-progress", "data"),
    Output("f-countries", "options"),
    Output("refresh-note", "children"),
    Input("btn-refresh", "n_clicks"),
    Input("f-commodity", "value"),
    prevent_initial_call=True,
)
def refresh_data(n, commodity):
    exports = load_weekly_exports(commodity)
    wasde = load_wasde_balance(commodity)
    progress = load_crop_progress(commodity)

    countries = sorted(exports["country"].unique().tolist())
    note = f"Loaded {len(exports):,} export rows for {commodity}."
    return exports.to_dict("records"), wasde.to_dict("records"), progress.to_dict("records"), countries, note


# -------------------------------------------------
# Overview KPIs & charts
# -------------------------------------------------
@app.callback(
    Output("kpi-net-sales", "children"),
    Output("kpi-shipments", "children"),
    Output("kpi-commit-progress", "children"),
    Output("kpi-top-buyer", "children"),
    Output("g-weekly-trend", "figure"),
    Output("g-map-destinations", "figure"),
    Input("store-exports", "data"),
    Input("store-wasde", "data"),
    Input("f-weeks", "value"),
    State("f-countries", "value"),
)

def update_overview(exports_data, wasde_data, week_range, country_filter):
    if not exports_data:
        raise dash.exceptions.PreventUpdate
    df = pd.DataFrame(exports_data)

    # filter by week range (relative from end)
    df_by_week = df.groupby("week", as_index=False)[["net_sales", "shipments"]].sum().sort_values("week")
    max_idx = len(df_by_week)
    start = max(0, week_range[0]-1)
    end = min(max_idx, week_range[1])
    df_window = df_by_week.iloc[start:end]

    latest_row = df_by_week.iloc[-1]
    net_latest = int(latest_row["net_sales"]) if not df_by_week.empty else 0
    ship_latest = int(latest_row["shipments"]) if not df_by_week.empty else 0

    # commitments vs wasde exports
    commitments = int(df_by_week["shipments"].sum())
    wasde = pd.DataFrame(wasde_data)
    wasde_exports = float(wasde.loc[wasde["component"]=="Exports", "current"].values[0]) if not wasde.empty else 0
    pct = f"{(commitments/(wasde_exports*1e6) * 100):.1f}%" if wasde_exports else "—"

    # top buyer ytd
    df_ytd = df
    if country_filter:
        df_ytd = df_ytd[df_ytd["country"].isin(country_filter)]
    top_buyer = df_ytd.groupby("country")["net_sales"].sum().sort_values(ascending=False).head(1)
    top_buyer_str = top_buyer.index[0] if len(top_buyer) else "—"

    # line figure
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Bar(name="Net Sales", x=df_window["week"], y=df_window["net_sales"]))
    fig_trend.add_trace(go.Scatter(name="Shipments", x=df_window["week"], y=df_window["shipments"], mode="lines+markers"))
    fig_trend.update_layout(margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h"))

    # map by destination (mock: use ISO name mapping where possible)
    df_country = df.groupby("country", as_index=False)["net_sales"].sum()
    fig_map = px.choropleth(df_country, locations="country", locationmode="country names", color="net_sales",
                            title="YTD Net Sales by Destination")
    fig_map.update_layout(margin=dict(l=0, r=0, t=40, b=0))

    return f"{net_latest:,}", f"{ship_latest:,}", pct, top_buyer_str, fig_trend, fig_map


# -------------------------------------------------
# Weekly Exports page
# -------------------------------------------------
@app.callback(
    Output("g-top-buyers", "figure"),
    Output("tbl-exports", "data"),
    Input("store-exports", "data"),
    Input("f-countries", "value"),
)

def update_exports(exports_data, country_filter):
    if not exports_data:
        raise dash.exceptions.PreventUpdate
    df = pd.DataFrame(exports_data)
    if country_filter:
        df = df[df["country"].isin(country_filter)]

    buyers = df.groupby("country", as_index=False)[["net_sales", "shipments"]].sum().sort_values("net_sales", ascending=False).head(10)
    fig = px.bar(buyers, x="country", y="net_sales", title="Top Buyers YTD (Net Sales)")

    # latest 12 weeks table
    latest_weeks = df["week"].drop_duplicates().sort_values().tail(12)
    tbl_df = df[df["week"].isin(latest_weeks)].sort_values(["week", "country"])
    tbl_df = tbl_df.assign(week=tbl_df["week"].dt.date.astype(str))

    return fig, tbl_df.to_dict("records")


# -------------------------------------------------
# Crop Progress page
# -------------------------------------------------
@app.callback(
    Output("g-progress-states", "figure"),
    Output("g-condition-trend", "figure"),
    Input("store-progress", "data"),
)

def update_progress(progress_data):
    if not progress_data:
        raise dash.exceptions.PreventUpdate
    df = pd.DataFrame(progress_data)

    # State snapshot (latest week)
    latest = df["week"].max()
    snap = df[df["week"] == latest][["state", "planted", "squaring", "setting_bolls"]]
    fig_states = px.bar(snap.melt("state"), x="state", y="value", color="variable", barmode="group",
                        title=f"Crop Stages by State — {latest.date()}")

    # Condition trend
    cond = df.groupby("week", as_index=False)["condition_good_excellent"].mean()
    fig_cond = px.line(cond, x="week", y="condition_good_excellent", title="Good/Excellent Condition (%)")

    return fig_states, fig_cond


# -------------------------------------------------
# WASDE page
# -------------------------------------------------
@app.callback(
    Output("g-balance-bars", "figure"),
    Output("g-exports-gauge", "figure"),
    Input("store-wasde", "data"),
    Input("store-exports", "data"),
)

def update_wasde(wasde_data, exports_data):
    if not wasde_data or not exports_data:
        raise dash.exceptions.PreventUpdate
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


# -------------------------------------------------
# Simple styles
# -------------------------------------------------
app.index_string = """
<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>USDA Agri Analytics</title>
    {%css%}
    <style>
        body { margin: 0; font-family: -apple-system, Segoe UI, Roboto, sans-serif; background: #fafafa; }
        .topbar { position: sticky; top: 0; z-index: 10; background: #fff; border-bottom: 1px solid #eee; padding: 10px 16px; display: flex; justify-content: space-between; }
        .title { font-weight: 600; }
        .muted { color: #666; font-size: 12px; }
        .container { display: grid; grid-template-columns: 280px 1fr; gap: 12px; padding: 12px; }
        .sidebar { background: #fff; border: 1px solid #eee; border-radius: 10px; padding: 12px; height: calc(100vh - 80px); position: sticky; top: 64px; overflow: auto; }
        .main { display: flex; flex-direction: column; gap: 12px; }
        .content { background: transparent; }
        .card { background: #fff; border: 1px solid #eee; border-radius: 10px; padding: 8px; }
        .kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
        .kpi { background: #fff; border: 1px solid #eee; border-radius: 10px; padding: 12px; }
        .kpi-title { font-size: 12px; color: #666; }
        .kpi-value { font-size: 22px; font-weight: 600; }
        .section-title { font-weight: 600; margin-bottom: 8px; }
        .chat-window { background: #fff; border: 1px solid #eee; border-radius: 10px; min-height: 300px; padding: 8px; margin-bottom: 8px; }
        .chat-input { display: grid; grid-template-columns: 1fr auto; gap: 8px; }
        @media (max-width: 1024px){ .container { grid-template-columns: 1fr; } .sidebar { position: static; height: auto; } .kpis { grid-template-columns: repeat(2, 1fr);} }
    </style>
</head>
<body>
    {%app_entry%}
    <footer>
        {%config%}
        {%scripts%}
        {%renderer%}
    </footer>
</body>
</html>
"""


# -------------------------------------------------
# Last updated note on load / refresh
# -------------------------------------------------
@app.callback(Output("last-updated", "children"), Input("store-exports", "data"))
def set_last_updated(_):
    return f"Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}"


if __name__ == "__main__":
    app.run(debug=True)
