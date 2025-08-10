import dash
from dash import Dash, html, dcc, Input, Output, State, ctx
from dash.dash_table import DataTable
import pandas as pd
from llm_bot import query_llm  # your actual bot function

# =========================
# App config / data sources
# =========================

def get_data(table_name: str) -> pd.DataFrame:
    # Temporary stub; replace with your actual data retrieval
    rows = [
        dict(table=table_name, section="Total Commitment", unit="Million 480 Bales", crop_year="2023",
             total=0.96, top11=0.13, top5=0.53, vietnam=0.27, china=0.65, turkey=0.44,
             indonasia=0.19, mexico=0.60, india=0.77, pakistan=0.72),
        dict(table=table_name, section="Commitment Untill Week 49", unit="Million 480 Bales", crop_year="2023",
             total=0.18, top11=0.09, top5=0.78, vietnam=0.74, china=0.56, turkey=0.07,
             indonasia=0.98, mexico=0.56, india=0.28, pakistan=0.11),
    ]
    return pd.DataFrame(rows)

TABLE_NAMES = [
    "Total Commitment and Weekly Net Sales",
    "Accumulated Exports and Weekly Shipments",
    "Upland NMY Commitment and Weekly Sales",
    "Pima NMY Commitment and Weekly Sales",
    "Pima Commitment and Weekly Sales",
    "Pima Accumulated Exports and Weekly Shipments",
    "Upland Commitment and Weekly Sales",
    "Upland Accumulated Exports and Weekly Shipments",
]

HEADER_COLORS = ["#E3F2FD", "#E8F5E9", "#FFF8E1", "#F3E5F5"]
PREFERRED_METRICS = [
    "total", "top11", "top5", "vietnam", "china", "turkey",
    "indonasia", "mexico", "india", "pakistan"
]
ROW_LABELS = {
    "total": "Total", "top11": "Top 11", "top5": "Top 5", "vietnam": "Vietnam",
    "china": "China", "turkey": "Turkey", "indonasia": "Indonesia",
    "mexico": "Mexico", "india": "India", "pakistan": "Pakistan"
}

# ====================================
# Reusable builder for multi-row table
# ====================================

def build_table(df: pd.DataFrame, title: str) -> html.Div:
    required = {"table", "section", "unit", "crop_year"}
    if not required.issubset(df.columns):
        return html.Div([html.H4(title), html.Div("Missing required columns")])

    for c in ["table", "section", "unit", "crop_year"]:
        df[c] = df[c].astype(str)

    metrics = [m for m in PREFERRED_METRICS if m in df.columns]
    if not metrics:
        return html.Div([html.H4(title), html.Div("No metric columns found.")])

    wide = pd.DataFrame({"Metric": [ROW_LABELS.get(m, m.title()) for m in metrics]})
    col_defs = [{"name": ["", "Metric", "", ""], "id": "Metric"}]

    for _, r in df.iterrows():
        t, s, u, y = r["table"], r["section"], r["unit"], r["crop_year"]
        col_id = "|".join([t, s, u, y])
        vals = [float(r[m]) if pd.notnull(r[m]) else None for m in metrics]
        wide[col_id] = vals
        col_defs.append({"name": [t, s, u, y], "id": col_id, "type": "numeric"})

    return html.Div([
        html.Div([html.H4(title)], className="card-head"),
        DataTable(
            data=wide.to_dict("records"),
            columns=col_defs,
            merge_duplicate_headers=True,
            style_table={"overflowX": "auto"},
            style_header_conditional=[
                {"if": {"header_index": i}, "backgroundColor": HEADER_COLORS[i]} for i in range(4)
            ]
        )
    ], className="card")

def build_usda_cards():
    return [build_table(get_data(name), name) for name in TABLE_NAMES]

# ============
# App layout
# ============

app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div([
    html.Div([
        html.H3("USDA Analytics Portal"),
    ], className="topbar"),

    dcc.Tabs(
        id="tabs", value="tab-usda",
        children=[
            dcc.Tab(label="USDA Tables", value="tab-usda"),
            dcc.Tab(label="Chatbot Query", value="tab-llm"),
        ]
    ),

    html.Div(id="tab-content", className="content")
])

# ================
# Tab content swap
# ================

@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "value")
)
def render_tab(tab_value):
    if tab_value == "tab-usda":
        return html.Div(build_usda_cards(), className="grid")
    elif tab_value == "tab-llm":
        return html.Div([
            html.H4("LLM Database Chatbot"),
            html.Div([
                dcc.Textarea(
                    id="llm-tab-question",
                    placeholder="Ask about shipments, commitments, countries, crops, weeks…",
                    style={"width": "100%", "height": "100px"}
                ),
                html.Button("Ask", id="llm-tab-submit", n_clicks=0),
            ], style={"marginBottom": "10px"}),

            html.Div([
                html.H5("Answer"),
                html.Pre(id="llm-tab-output", style={"whiteSpace": "pre-wrap", "border": "1px solid #ccc", "padding": "8px"}),
            ]),

        ], style={"maxWidth": "800px", "margin": "auto"})
    return html.Div()

# =========================
# LLM tab callback
# =========================

@app.callback(
    Output("llm-tab-output", "children"),
    Input("llm-tab-submit", "n_clicks"),
    State("llm-tab-question", "value"),
    prevent_initial_call=True
)
def handle_llm_tab(n, question):
    if not question:
        return "Please enter a question."
    return query_llm(question)

if __name__ == "__main__":
    app.run(debug=True)
