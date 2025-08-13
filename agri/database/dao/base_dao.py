from agri.database.connections import engine
import pandas as pd

def fetch_df(query: str, params: dict = None) -> pd.DataFrame:
    """Run SQL and return DataFrame."""
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params=params)