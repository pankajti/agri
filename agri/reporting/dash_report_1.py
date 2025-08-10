import dash
from dash import html
from dash.dash_table import DataTable, Format
import pandas as pd
from pathlib import Path
from agri.reporting.usda_weekly_export_sales_report import get_data

# ====== CONFIG ======
tame_names = [
    "Upland NMY Commitment and Weekly Sales",
    "Upland NMY Commitment and Weekly Sales_2",
    "Upland NMY Commitment and Weekly Sales_3",
]

HEADER_COLORS = ["#E3F2FD", "#E8F5E9", "#FFF8E1", "#F3E5F5"]  # Table, Section, Unit, Crop Year
PREFERRED_METRICS = [
    "total", "top11", "top5", "vietnam", "china", "turkey",
    "indonasia", "mexico", "india", "pakistan"
]
ROW_LABELS = {
    "total": "Total",
    "top11": "Top 11",
    "top5": "Top 5",
    "vietnam": "Vietnam",
    "china": "China",
    "turkey": "Turkey",
    "indonasia": "Indonesia",
    "mexico": "Mexico",
    "india": "India",
    "pakistan": "Pakistan",
}

def build_table(df: pd.DataFrame, title: str) -> html.Div:
    """Builds one DataTable card from a dataframe."""
    required = {"table", "section", "unit", "crop_year"}
    if not required.issubset(df.columns):
        return html.Div([
            html.H4(title, style={"margin": "0 0 8px"}),
            html.Div(f"Missing required columns: {sorted(required - set(df.columns))}",
                     style={"color": "crimson"})
        ], className="card")

    # Coerce to string for header levels
    for c in ["table", "section", "unit", "crop_year"]:
        df[c] = df[c].astype(str)

    # Keep only metrics present in this CSV
    metrics = [m for m in PREFERRED_METRICS if m in df.columns]
    if not metrics:
        return html.Div([
            html.H4(title, style={"margin": "0 0 8px"}),
            html.Div("No metric columns found.", style={"color": "crimson"})
        ], className="card")

    # Start wide table with Metric column
    wide = pd.DataFrame({"Metric": [ROW_LABELS.get(m, m.title()) for m in metrics]})
    col_defs = [{"name": ["", "Metric", "", ""], "id": "Metric"}]

    # Add each data column from (table, section, unit, crop_year)
    for _, r in df.iterrows():
        t, s, u, y = r["table"], r["section"], r["unit"], r["crop_year"]
        col_id = "|".join([t, s, u, y])  # unique string ID
        vals = []
        for m in metrics:
            try:
                vals.append(float(r[m]))
            except Exception:
                vals.append(None)
        wide[col_id] = vals
        col_defs.append({
            "name": [t, s, u, y],  # stacked headers
            "id": col_id,
            "type": "numeric",
            #"format": Format(precision=2)
        })

    table = DataTable(
        data=wide.to_dict("records"),
        columns=col_defs,
        merge_duplicate_headers=True,
        style_table={"overflowX": "auto"},
        style_data={"border": "1px solid #e5e7eb"},
        style_cell={
            "padding": "8px",
            "fontSize": "14px",
            "whiteSpace": "normal",
            "minWidth": "120px",
            "textAlign": "center",
        },
        style_cell_conditional=[
            {"if": {"column_id": "Metric"}, "textAlign": "left", "minWidth": "180px"}
        ],
        style_header={
            "fontWeight": 600,
            "border": "1px solid #ccc",
            "textAlign": "center",
        },
        style_header_conditional=[
            {"if": {"header_index": 0}, "backgroundColor": HEADER_COLORS[0]},
            {"if": {"header_index": 1}, "backgroundColor": HEADER_COLORS[1]},
            {"if": {"header_index": 2}, "backgroundColor": HEADER_COLORS[2]},
            {"if": {"header_index": 3}, "backgroundColor": HEADER_COLORS[3]},
        ],
    )

    return html.Div(
        [html.H4(title, style={"margin": "0 0 8px"}), table],
        className="card"
    )

# Build one card per CSV
cards = []
for table_name in tame_names:
    try:
        df = get_data(table_name=table_name)
        title = table_name
        cards.append(build_table(df, title))
    except Exception as e:
        cards.append(html.Div([
            html.H4(table_name, style={"margin": "0 0 8px"}),
            html.Div(f"Failed to read CSV: {e}", style={"color": "crimson"})
        ], className="card"))

app = dash.Dash(__name__)
app.layout = html.Div(
    className="page",
    children=[
        html.H3("USDA Multi-row Header Tables (Two-Column Layout)",
                style={"margin": "0 0 14px"}),
        html.Div(cards, className="grid")
    ]
)
server = app.server
if __name__ == "__main__":
    app.run(debug=True)
