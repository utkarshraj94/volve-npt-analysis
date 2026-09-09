import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()

def get_engine():
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        database=os.environ["DB_NAME"],
    )
    return create_engine(url)

if __name__ == "__main__":
    engine = get_engine()
    with engine.connect() as conn:
        print("Connected OK:", conn.execute(text("SELECT version()")).fetchone())