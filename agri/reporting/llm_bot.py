# llm_bot.py
import os
import re
from agri.config.config import load_env
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage

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

def enforce_readonly_and_limit(sql: str) -> str:
    if DANGEROUS_SQL.search(sql):
        raise ValueError("Blocked potentially dangerous SQL.")
    s = sql.strip().rstrip(";")
    if re.match(r"(?is)^\s*select\b", s) and not re.search(r"(?is)\blimit\s+\d+\b", s):
        s = f"{s}\nLIMIT {DEFAULT_LIMIT}"
    return s + ";"

SYSTEM_INSTRUCTIONS = f"""
You are a SQL analyst for a PostgreSQL database.

Tables and joins:
1. usda_weekly_export_sales
   Columns (must be double-quoted):
     "commodityCode", "countryCode", "weeklyExports", "accumulatedExports",
     "outstandingSales", "grossNewSales", "currentMYNetSales",
     "currentMYTotalCommitment", "nextMYOutstandingSales", "nextMYNetSales",
     "weekEndingDate", market_year

2. commodities — "commodityCode", "commodityName"
3. countries  — "countryCode", "countryName"

Joins:
- usda_weekly_export_sales."commodityCode" = commodities."commodityCode"
- usda_weekly_export_sales."countryCode"   = countries."countryCode"

Use SUM("weeklyExports") for "highest export" unless otherwise specified.
Always double-quote CamelCase identifiers.
"""

prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=SYSTEM_INSTRUCTIONS),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])

# Build once and reuse
db = SQLDatabase.from_uri(
    os.environ["DATABASE_URL"],
    include_tables=ALLOWED_TABLES,
    sample_rows_in_table_info=3
)
original_run = db.run
def safe_run(sql: str, *args, **kwargs):
    return original_run(enforce_readonly_and_limit(sql), *args, **kwargs)
db.run = safe_run  # type: ignore

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
tools = toolkit.get_tools()
agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

chat_history = []

def query_llm(question: str) -> str:
    global chat_history
    try:
        resp = executor.invoke({"input": question, "chat_history": chat_history})
        answer = resp.get("output", "")
        chat_history.extend([
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer}
        ])
        return answer
    except Exception as e:
        return f"[Error] {e}"


if __name__ == '__main__':
    resp = query_llm("which is the country with highest weekly export in july 2025 for each commodites?")
    print(resp)