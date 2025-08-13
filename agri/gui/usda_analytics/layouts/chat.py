# chat.py
from dash import html, dcc, Input, Output, State
import dash
from agri.reporting.llm_bot import query_llm  # your file

def layout():
    return html.Div([
        html.H4("USDA Data Chatbot", style={"textAlign": "center", "marginBottom": "10px"}),

        dcc.Loading(
            id="llm-loading",
            type="dot",
            children=html.Div(
                id="llm-chat-window",
                className="chat-window"
            )
        ),

        html.Div([
            dcc.Textarea(
                id="llm-input",
                placeholder="Ask me about exports, commitments, countries, crops, weeks...",
                style={"flexGrow": "1", "height": "50px", "borderRadius": "5px",
                       "padding": "10px", "resize": "none", "border": "1px solid #ccc"}
            ),
            html.Button("Ask", id="llm-submit", className="btn btn-primary"),
            html.Button("Clear", id="llm-clear", className="btn btn-danger")
        ], style={"display": "flex", "gap": "10px", "marginTop": "8px"}),

        dcc.Store(id="llm-chat-history", storage_type="session",
                  data=[{"role": "bot", "content": "Hello! I can query USDA exports database for you."}])
    ])


def register_callbacks(app):

    @app.callback(
        Output("llm-chat-history", "data"),
        Output("llm-input", "value"),
        Input("llm-submit", "n_clicks"),
        Input("llm-clear", "n_clicks"),
        State("llm-input", "value"),
        State("llm-chat-history", "data"),
        State("f-commodity", "value"),       # NEW
        State("f-marketing-year", "value"),  # NEW
        State("f-countries", "value"),       # NEW
        prevent_initial_call=True
    )
    def update_chat(submit_clicks, clear_clicks, question, history,
                    commodity, marketing_year, countries):
        trigger = dash.ctx.triggered_id

        if trigger == "llm-clear":
            return [{"role": "bot", "content": "Hello! I can query USDA exports database for you."}], ""

        if trigger == "llm-submit" and question and question.strip():
            history.append({"role": "user", "content": question.strip()})

            # Build contextual question
            context_parts = []
            if commodity:
                context_parts.append(f"Commodity: {commodity}")
            if marketing_year:
                context_parts.append(f"Marketing Year: {marketing_year}")
            if countries:
                context_parts.append(f"Destinations: {', '.join(countries)}")

            if context_parts:
                context_str = " | ".join(context_parts)
                full_question = f"Context: {context_str}\nQuestion: {question.strip()}"
            else:
                full_question = question.strip()

            reply = query_llm(full_question)
            history.append({"role": "bot", "content": reply})
            return history, ""

        return dash.no_update, ""

    @app.callback(
        Output("llm-chat-window", "children"),
        Input("llm-chat-history", "data")
    )
    def render_chat(history):
        def style_msg(role):
            return {
                "alignSelf": "flex-start" if role == "bot" else "flex-end",
                "backgroundColor": "#eef2ff" if role == "bot" else "#e5f9f0",
                "border": "1px solid #dbe3ff" if role == "bot" else "#c7f0dc"
            }
        return [
            html.Div(
                m["content"],
                style={
                    **style_msg(m["role"]),
                    "borderRadius": "12px",
                    "padding": "10px 12px",
                    "margin": "4px 0",
                    "maxWidth": "75%",
                    "whiteSpace": "pre-wrap"
                }
            ) for m in history
        ]
