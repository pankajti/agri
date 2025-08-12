import dash
from dash import Dash, html, dcc, Input, Output, State
from agri.reporting.llm_bot import query_llm

app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# ---------------- Shared / Persistent Stores ----------------
# Put the store outside the tab so switching tabs doesn't wipe it.
app.layout = html.Div([
    # App bar
    html.Div([
        html.H3("USDA Analytics Portal", style={"margin": 0})
    ], style={
        "padding": "12px 16px",
        "borderBottom": "1px solid #eee",
        "background": "#fff",
        "position": "sticky",
        "top": 0,
        "zIndex": 10
    }),

    # Tabs
    dcc.Tabs(
        id="tabs",
        value="tab-llm",
        children=[dcc.Tab(label="Chatbot Query", value="tab-llm")]
    ),

    # Page content
    html.Div(id="tab-content", className="content"),

    # Chat history stored in session storage so reloads keep it
    dcc.Store(
        id="llm-chat-history",
        storage_type="session",
        data=[{"role": "bot", "content": "Hello! I'm here to help you with USDA data. What would you like to know?"}]
    ),

    # Dummy target for clientside callbacks (so we don't overwrite real content)
    html.Div(id="noop-target", style={"display": "none"})
], style={"fontFamily": "Segoe UI, sans-serif"})


# ---------------- Chatbot Tab Layout ----------------
def chatbot_layout():
    return html.Div([
        html.H4("USDA Data Chatbot", style={"textAlign": "center", "marginBottom": "10px"}),

        # Spinner + Chat Window
        dcc.Loading(
            id="llm-loading",
            type="default",
            children=html.Div(
                id="llm-chat-window",
                style={
                    "border": "1px solid #ddd",
                    "borderRadius": "8px",
                    "padding": "10px",
                    "height": "400px",
                    "overflowY": "auto",
                    "marginBottom": "15px",
                    "backgroundColor": "#f9f9f9",
                    "display": "flex",
                    "flexDirection": "column"
                }
            )
        ),

        # Input Area
        html.Div([
            dcc.Textarea(
                id="llm-tab-question",
                placeholder="Ask about shipments, commitments, countries, crops, weeks...",
                style={
                    "flexGrow": "1",
                    "height": "50px",
                    "borderRadius": "5px",
                    "padding": "10px",
                    "resize": "none",
                    "border": "1px solid #ccc"
                }
            ),
            html.Button(
                "Ask", id="llm-tab-submit", n_clicks=0,
                style={"height": "50px", "backgroundColor": "#007bff", "color": "white",
                       "border": "none", "borderRadius": "5px", "padding": "0 20px", "cursor": "pointer"}
            ),
            html.Button(
                "Clear", id="llm-tab-clear", n_clicks=0,
                style={"height": "50px", "backgroundColor": "#dc3545", "color": "white",
                       "border": "none", "borderRadius": "5px", "padding": "0 20px", "cursor": "pointer"}
            )
        ], style={"display": "flex", "gap": "10px", "alignItems": "center"}),

        # Invisible scroll anchor (only one place in the tree)
        html.Div(id="scroll-anchor", style={"height": "1px"})
    ], style={"maxWidth": "800px", "margin": "auto", "padding": "20px"})


# ---------------- Tab Router ----------------
@app.callback(Output("tab-content", "children"), Input("tabs", "value"))
def render_tab(tab_value):
    if tab_value == "tab-llm":
        return chatbot_layout()
    return html.Div()


# ---------------- Chat update ----------------
@app.callback(
    Output("llm-chat-history", "data"),
    Output("llm-tab-question", "value"),
    Output("llm-tab-submit", "disabled"),
    Input("llm-tab-submit", "n_clicks"),
    Input("llm-tab-clear", "n_clicks"),
    State("llm-tab-question", "value"),
    State("llm-chat-history", "data"),
    prevent_initial_call=True
)
def update_chat(send_clicks, clear_clicks, question, history):
    trigger = dash.ctx.triggered_id

    if trigger == "llm-tab-clear":
        return (
            [{"role": "bot", "content": "Hello! I'm here to help you with USDA data. What would you like to know?"}],
            "",
            False
        )

    if trigger == "llm-tab-submit":
        q = (question or "").strip()
        if not q:
            return dash.no_update, "", False

        # append user message
        new_history = (history or []) + [{"role": "user", "content": q}]

        # call model
        try:
            reply = query_llm(q)
        except Exception as e:
            reply = f"❌ Sorry, I encountered an error: {e}"

        new_history.append({"role": "bot", "content": reply})

        # keep only last N messages to avoid bloat
        MAX_MSG = 100
        if len(new_history) > MAX_MSG:
            new_history = new_history[-MAX_MSG:]

        # clear input, re-enable Ask
        return new_history, "", False

    return dash.no_update, "", False


# ---------------- Render Chat Window ----------------
@app.callback(
    Output("llm-chat-window", "children"),
    Input("llm-chat-history", "data")
)
def render_chat_window(history):
    def style_msg(role):
        if role == "bot":
            return {"alignSelf": "flex-start", "backgroundColor": "#eef2ff", "border": "1px solid #dbe3ff"}
        return {"alignSelf": "flex-end", "backgroundColor": "#e5f9f0", "border": "1px solid #c7f0dc"}

    chat_bubbles = [
        html.Div(
            m.get("content", ""),
            style={
                **style_msg(m.get("role")),
                "borderRadius": "12px",
                "padding": "10px 12px",
                "margin": "4px 0",
                "maxWidth": "75%",
                "whiteSpace": "pre-wrap"
            }
        )
        for m in (history or [])
    ]
    # keep a single anchor in the tree
    chat_bubbles.append(html.Div(style={"height": "1px"}))
    return chat_bubbles


# ---------------- Auto-scroll Client Script ----------------
# Use a "noop" hidden div so we never overwrite real content.
app.clientside_callback(
    """
    function(children) {
        const anchor = document.getElementById("scroll-anchor");
        if (anchor) {
            anchor.scrollIntoView({behavior: "smooth", block: "end"});
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("noop-target", "children", allow_duplicate=True),
    Input("llm-chat-window", "children"),
    prevent_initial_call=True
)


if __name__ == "__main__":
    app.run(debug=True)
