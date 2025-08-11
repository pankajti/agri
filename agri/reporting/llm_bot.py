# llm_bot.py
import os
import re
from typing import Dict, Any, List

from agri.config.config import load_env
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, AIMessage, HumanMessage
from langchain_ollama.chat_models import ChatOllama
# --- Configuration & Setup ---

load_env()

ALLOWED_TABLES = [
    "usda_weekly_export_sales",
    "commodities",
    "countries"
]
DEFAULT_LIMIT = 200
DANGEROUS_SQL = re.compile(
    r"\b(ALTER|CREATE|DROP|TRUNCATE|INSERT|UPDATE|DELETE|GRANT|REVOKE|VACUUM|ANALYZE)\b",
    re.IGNORECASE,
)


# --- Utility Functions ---

def enforce_readonly_and_limit(sql: str) -> str:
    """Blocks dangerous SQL commands and adds a LIMIT clause to SELECT statements."""
    if DANGEROUS_SQL.search(sql):
        raise ValueError("Blocked potentially dangerous SQL command.")
    s = sql.strip().rstrip(";")
    if s.lower().startswith("select") and not re.search(r"(?is)\blimit\s+\d+\b", s):
        s = f"{s}\nLIMIT {DEFAULT_LIMIT}"
    return s + ";"


# --- LangChain Setup ---

def setup_langchain_agent() -> AgentExecutor:
    """Sets up and returns a configured LangChain SQL agent."""
    db = SQLDatabase.from_uri(
        os.environ["DATABASE_URL"],
        include_tables=ALLOWED_TABLES,
        sample_rows_in_table_info=3
    )

    # Wrap the original run method for security
    original_run = db.run

    def safe_run(sql: str, *args: Any, **kwargs: Any) -> str:
        return original_run(enforce_readonly_and_limit(sql), *args, **kwargs)

    db.run = safe_run  # type: ignore

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    #llm = ChatOllama(model="llama3.2")


    SYSTEM_INSTRUCTIONS = f"""
    You are a SQL analyst for a PostgreSQL database.

    Tables and joins:
    1. usda_weekly_export_sales
       Columns: "commodityCode", "countryCode", "weeklyExports", "accumulatedExports",
                "outstandingSales", "grossNewSales", "currentMYNetSales",
                "currentMYTotalCommitment", "nextMYOutstandingSales", "nextMYNetSales",
                "weekEndingDate", market_year

    2. commodities — "commodityCode", "commodityName"
    3. countries  — "countryCode", "countryName"

    Joins:
    - usda_weekly_export_sales."commodityCode" = commodities."commodityCode"
    - usda_weekly_export_sales."countryCode"   = countries."countryCode"

    Use SUM("weeklyExports") for "highest export" unless otherwise specified.
    Always double-quote identifiers, especially those with mixed case (e.g., "commodityCode").
    Ensure all queries are valid PostgreSQL syntax.
    """

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=SYSTEM_INSTRUCTIONS),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()
    agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=prompt)

    return AgentExecutor(agent=agent, tools=tools, verbose=False)


# --- Global State & Main Function ---

executor = setup_langchain_agent()
chat_history: List[Any] = []


def query_llm(question: str) -> str:
    """Invokes the LangChain agent with a user question and updates chat history."""
    global chat_history
    try:
        response = executor.invoke({"input": question, "chat_history": chat_history})
        answer = response.get("output", "I could not process your request.")

        # Update history with LangChain-compatible message objects
        chat_history.append(HumanMessage(content=question))
        chat_history.append(AIMessage(content=answer))

        return answer
    except ValueError as e:
        # Catch our specific security error
        return f"[Security Error] {e}"
    except Exception as e:
        # Catch other, more general errors
        return f"[Error] An unexpected error occurred: {e}"


if __name__ == '__main__':
    # A simple example of how to use the function
    print("USDA Data Chatbot - Ask a question or type 'exit' to quit.")
    while True:
        user_question = input("You: ")
        if user_question.lower() == 'exit':
            break
        response = query_llm(user_question)
        print(f"Bot: {response}\n")