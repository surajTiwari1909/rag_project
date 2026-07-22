from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.sqlalchemy_database_uri,
    echo=settings.db_echo,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def check_database_connection() -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


#   - engine -> yes, this is the layer that includes and manages the pool
#   - SessionLocal -> not the pool itself; it creates session objects that use the pool
#   - get_db_session() -> not the pool either; it is just a safe wrapper around session usage


'''
flow
 One typical flow looks like this:

  1. FastAPI route needs the database.
  2. get_db_session() creates a session from SessionLocal.
  3. That session asks the engine for a connection when it actually needs one.
  4. The engine gives it a connection from the pool.
  5. Your code runs a query or insert through the session.
  6. When the work is done, the session is closed.
  7. The connection is returned to the pool for reuse.

  So the important distinction is:

  - the session is what your app code uses
  - the pool is what the engine manages underneath
  - closing the session usually does not destroy the connection; it returns it to the pool

  Very small mental model:

  - engine = manages reusable DB connections
  - session = your current unit of DB work
  - close() = release resources and hand the connection back

  Example shape:

  def get_db_session():
      session = SessionLocal()
      try:
          yield session
      finally:
          session.close()

  That means:

  - open a session
  - let the route/service use it
  - always close it afterward

  If you want, we can move to Step 6 now and I’ll explain the startup connection check before making any change.



'''