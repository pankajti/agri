import dash
from dash import Dash, dcc, html, Input, Output, State
import pandas as pd

from agri.gui.usda_analytics.data.loaders import load_weekly_exports, load_wasde_balance, load_crop_progress,get_marketing_years
from agri.gui.usda_analytics.layouts.overview import layout as overview_layout, register_callbacks as register_overview
from agri.gui.usda_analytics.layouts.exports import layout as exports_layout, register_callbacks as register_exports
from agri.gui.usda_analytics.layouts.progress import layout as progress_layout, register_callbacks as register_progress
from agri.gui.usda_analytics.layouts.wasde import layout as wasde_layout, register_callbacks as register_wasde
from agri.gui.usda_analytics.layouts.chat import layout as chat_layout, register_callbacks as register_chat
import plotly.io as pio
pio.templates.default = "plotly_white"
commodities = ["Cotton- Am Pima", "Wheat", "Corn", "All Upland Cotton"]
marketing_years = get_marketing_years(commodities[0])
def create_app() -> Dash:
    app = Dash(__name__, suppress_callback_exceptions=True)
    server = app.server

    # --------------- Base layout ---------------
    app.layout = html.Div([
        html.Div([
            html.Div("USDA Agri Analytics", className="title"),
            html.Div(id="last-updated", className="muted")
        ], className="topbar"),

        html.Div([
            # Sidebar
            html.Div([
                html.Label("Commodity"),
                dcc.Dropdown(id="f-commodity", options=commodities, value=commodities[0],
                             clearable=False),

                html.Label("Marketing Year"),
                dcc.Dropdown(id="f-marketing-year", options=marketing_years, value= marketing_years[0], clearable=False),

                html.Label("Destinations"),
                dcc.Dropdown(id="f-countries", multi=True),

                #html.Label("Week Range"),
                html.Label("Weeks"),
                dcc.RadioItems(
                    id="f-week-mode",
                    options=[{"label": "Last N weeks", "value": "last_n"},
                             {"label": "Custom range", "value": "range"}],
                    value="last_n",
                    labelStyle={"display": "inline-block", "marginRight": "10px"}
                ),

                # Last N weeks controls
                html.Div([
                    dcc.Input(
                        id="f-last-n", type="number", min=1, max=52, step=1, value=12,
                        style={"width": "90px", "marginRight": "8px"}
                    ),
                    html.Span("weeks", className="muted"),
                    html.Div([
                        html.Button("4", id="chip-4", className="chip"),
                        html.Button("8", id="chip-8", className="chip"),
                        html.Button("12", id="chip-12", className="chip"),
                        html.Button("YTD", id="chip-ytd", className="chip"),
                    ], style={"marginTop": "8px", "display": "flex", "gap": "6px", "flexWrap": "wrap"})
                ], id="wrap-last-n"),

                # Custom date range controls
                html.Div([
                    dcc.DatePickerRange(
                        id="f-date-range",
                        minimum_nights=0,
                        display_format="YYYY-MM-DD"
                    ),
                    html.Div("Tip: FAS weeks end on Thursday; the filter will snap to week-ending dates.",
                             className="muted", style={"marginTop": "6px"})
                ], id="wrap-date-range", style={"display": "none"}),

                # unified resolved week filter
                dcc.Store(id="store-week-filter"),

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

            # Main
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

    # --------------- Routing ---------------
    @app.callback(Output("tab-content", "children"), Input("tabs", "value"))
    def render_tab(tab):
        if tab == "tab-overview":
            return overview_layout()
        if tab == "tab-exports":
            return exports_layout()
        if tab == "tab-progress":
            return progress_layout()
        if tab == "tab-wasde":
            return wasde_layout()
        if tab == "tab-chat":
            return chat_layout()
        return html.Div()

    # --------------- Data refresh ---------------
    @app.callback(
        Output("store-exports", "data"),
        Output("store-wasde", "data"),
        Output("store-progress", "data"),
        Output("f-countries", "options"),
        Output("refresh-note", "children"),
        Input("btn-refresh", "n_clicks"),
        Input("f-commodity", "value"),
        State("f-marketing-year", "value"),

        prevent_initial_call=True,
    )
    def refresh_data(n, commodity,my):
        exports = load_weekly_exports(commodity)
        if my:
            exports = exports[exports["my"] == my]
        wasde = load_wasde_balance(commodity)
        progress = load_crop_progress(commodity)

        countries = sorted(exports["country"].unique().tolist())
        note = f"Loaded {len(exports):,} export rows for {commodity}."
        return exports.to_dict("records"), wasde.to_dict("records"), progress.to_dict("records"), countries, note

    # --------------- Last updated note ---------------
    @app.callback(Output("last-updated", "children"), Input("store-exports", "data"))
    def set_last_updated(_):
        return f"Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}"

    # --------------- Register page-specific callbacks ---------------
    register_overview(app)
    register_exports(app)
    register_progress(app)
    register_wasde(app)
    register_chat(app)
    from datetime import timedelta
    import pandas as pd
    import numpy as np
    from dash import no_update

    # Toggle which control is visible
    @app.callback(
        Output("wrap-last-n", "style"),
        Output("wrap-date-range", "style"),
        Input("f-week-mode", "value"),
    )
    def _toggle_week_controls(mode):
        if mode == "last_n":
            return {"display": "block"}, {"display": "none"}
        return {"display": "none"}, {"display": "block"}

    # Quick chips -> set last N
    @app.callback(
        Output("f-last-n", "value"),
        Input("chip-4", "n_clicks"),
        Input("chip-8", "n_clicks"),
        Input("chip-12", "n_clicks"),
        Input("chip-ytd", "n_clicks"),
        prevent_initial_call=True
    )
    def _chip_lastn(c4, c8, c12, cytd):
        trg = dash.ctx.triggered_id
        if trg == "chip-4": return 4
        if trg == "chip-8": return 8
        if trg == "chip-12": return 12
        if trg == "chip-ytd": return 52
        return no_update

    # Resolve week filter into a concrete (start_date, end_date) window
    @app.callback(
        Output("store-week-filter", "data"),
        Input("f-week-mode", "value"),
        Input("f-last-n", "value"),
        Input("f-date-range", "start_date"),
        Input("f-date-range", "end_date"),
        Input("store-exports", "data"),
    )
    def _resolve_week_filter(mode, last_n, start_date, end_date, exports_data):
        if not exports_data:
            raise dash.exceptions.PreventUpdate

        df = pd.DataFrame(exports_data)
        weeks = pd.to_datetime(df["week"]).dropna().sort_values().unique()
        if weeks.size == 0:
            raise dash.exceptions.PreventUpdate

        # FAS weeks end on Thursday; snap both ends to actual week dates we have
        def snap(dt_str, fallback):
            if not dt_str:
                return fallback
            dt = pd.to_datetime(dt_str)
            # find the last week date <= dt
            arr = weeks[weeks <= np.datetime64(dt)]
            return arr[-1] if arr.size else weeks[0]

        if mode == "last_n":
            n = int(last_n or 12)
            n = max(1, min(n, 104))  # allow up to 2 years if desired
            end = weeks[-1]
            start_idx = max(0, weeks.size - n)
            start = weeks[start_idx]
            return {"start": pd.to_datetime(start).strftime("%Y-%m-%d"),
                    "end": pd.to_datetime(end).strftime("%Y-%m-%d")}

        # custom range
        start = snap(start_date, weeks[0])
        end = snap(end_date, weeks[-1])
        if start > end:
            start, end = end, start
        return {"start": pd.to_datetime(start).strftime("%Y-%m-%d"),
                "end": pd.to_datetime(end).strftime("%Y-%m-%d")}

    # --------------- Index HTML (inline CSS handled via assets/style.css) ---------------
    app.index_string = (
        """
        <!DOCTYPE html>
        <html>
        <head>
            {%metas%}
            <title>USDA Agri Analytics</title>
            {%css%}
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
    )
    return app

