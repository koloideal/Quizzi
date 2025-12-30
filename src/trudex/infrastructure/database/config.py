from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine


def create_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url, echo=False)


def create_session_maker(engine: AsyncEngine) -> async_sessionmaker:
    return async_sessionmaker(engine, expire_on_commit=False)
