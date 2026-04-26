import os
import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError


def wait_for_db(max_retries: int = 30, delay_seconds: int = 2) -> None:
    database_url = os.getenv(
        "DATABASE_URL", "postgresql+psycopg2://postgres:password@localhost:5432/task_manager"
    )
    engine = create_engine(database_url)

    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            print("Database is ready")
            return
        except OperationalError:
            print(f"Database not ready (attempt {attempt}/{max_retries}), retrying...")
            time.sleep(delay_seconds)

    raise RuntimeError("Database connection failed after max retries")


if __name__ == "__main__":
    wait_for_db()
