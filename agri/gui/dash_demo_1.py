import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.express as px

from langchain_ollama import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain.agents.agent_types import AgentType

from langchain_community.agent_toolkits import SQLDatabaseToolkit

# --- 1. SET UP THE LANGCHAIN SQL AGENT ---

# Create a dummy USDA export/import data table for demonstration
data = {
    'country': ['China', 'Mexico', 'Canada', 'Japan', 'South Korea', 'Germany'],
    'exports_usd': [28700000000, 28300000000, 27500000000, 14000000000, 8900000000, 3100000000],
    'imports_usd': [5500000000, 32000000000, 24000000000, 7800000000, 6500000000, 1100000000],
    'year': [2023, 2023, 2023, 2023, 2023, 2023],
    'commodity': ['Soybeans', 'Fruits', 'Grains', 'Beef', 'Pork', 'Dairy']
}
df = pd.DataFrame(data)

# Load the DataFrame into an in-memory SQLite database

db_uri = "sqlite:///:memory:"
db = SQLDatabase.from_uri(db_uri)
df.to_sql("usda_data", db_uri, index=False)


# Initialize the LLM from Ollama
llm = ChatOllama(model="llama3.1")

# Create the SQL Database Toolkit
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

# Create the SQL Agent
agent_executor = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
)

# --- 2. BUILD THE PLOTLY DASHBOARD ---

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout of the dashboard
app.layout = html.Div([
    html.H1("USDA Trade Data Dashboard with Llama 3.1", style={'textAlign': 'center'}),
    html.Hr(),

    html.Div([
        html.H3("Ask a question about the data:", style={'textAlign': 'center'}),
        dcc.Textarea(
            id='user-query-input',
            placeholder='e.g., "Which country had the highest total exports in 2023?"',
            style={'width': '80%', 'height': 100, 'margin': 'auto', 'display': 'block'}
        ),
        html.Button(
            'Get Insights',
            id='submit-button',
            n_clicks=0,
            style={'margin': '20px auto', 'display': 'block'}
        ),
    ]),
    html.Hr(),

    html.Div([
        html.H3("LLM Answer:", style={'textAlign': 'center'}),
        html.Div(
            id='llm-output-container',
            children=html.P('Answer will appear here.'),
            style={'padding': '20px', 'border': '1px solid #ddd', 'width': '80%', 'margin': 'auto'}
        )
    ]),
    html.Hr(),

    html.Div([
        html.H3("Data Preview and Visualization:", style={'textAlign': 'center'}),
        html.Div(
            dcc.Graph(
                id='exports-bar-chart',
                figure=px.bar(df.sort_values('exports_usd', ascending=False), x='country', y='exports_usd',
                              title='Exports by Country (2023)')
            ),
            style={'width': '80%', 'margin': 'auto'}
        ),
        html.Div(
            dcc.Graph(
                id='imports-bar-chart',
                figure=px.bar(df.sort_values('imports_usd', ascending=False), x='country', y='imports_usd',
                              title='Imports by Country (2023)')
            ),
            style={'width': '80%', 'margin': 'auto', 'marginTop': '20px'}
        ),
    ])
])


# --- 3. DEFINE CALLBACKS FOR INTERACTIVITY ---

@app.callback(
    Output('llm-output-container', 'children'),
    Input('submit-button', 'n_clicks'),
    State('user-query-input', 'value')
)
def update_output(n_clicks, user_query):
    """
    This callback function is triggered when the 'Get Insights' button is clicked.
    It takes the user's query, passes it to the LangChain agent, and displays the LLM's response.
    """
    if n_clicks > 0 and user_query:
        try:
            response = agent_executor.invoke({"input": user_query})
            return html.P(response["output"])
        except Exception as e:
            return html.P(f"An error occurred: {e}", style={'color': 'red'})

    return "Answer will appear here."


# --- 4. RUN THE APP ---
server = app.server

if __name__ == '__main__':
    app.run(debug=True, port=8990)