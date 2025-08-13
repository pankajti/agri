from agri.config.config import DATABASE_URL
from sqlalchemy.orm import sessionmaker

from sqlalchemy import create_engine

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

import os
import pandas as pd
from sqlalchemy import create_engine

# Read connection string from env var for safety
# Example: export DATABASE_URL="postgresql+psycopg2://user:pass@host:5432/dbname"
DB_URL = os.environ.get("DATABASE_URL")

engine = create_engine(DB_URL)

