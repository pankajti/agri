import dotenv
import os

def load_env():
    try:
        dotenv.load_dotenv("/Users/pankajti/dev/git/agri/agri/config/.env")
    except Exception as e:
        print("error", str(e))
load_env()
DATABASE_URL = os.environ['DATABASE_URL']
