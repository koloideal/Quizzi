import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BotConfig:
    token: str


@dataclass
class DatabaseConfig:
    host: str
    port: int | str
    user: str
    password: str
    database: str
    
    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class AppConfig:
    bot: BotConfig
    database: DatabaseConfig
    
    @classmethod
    def from_toml(cls, path: str | Path = "config.toml") -> "AppConfig":
        with open(path, "rb") as f:
            data: dict[str, dict[str, str]] = tomllib.load(f)
        
        bot_data: dict[str, str] = data["bot"]
        db_data: dict[str, str] = data["database"]
        
        return cls(
            bot=BotConfig(
                token=bot_data["token"]
            ),
            database=DatabaseConfig(
                host=db_data["host"],
                port=db_data["port"],
                user=db_data["user"],
                password=db_data["password"],
                database=db_data["database"]
            )
        )
