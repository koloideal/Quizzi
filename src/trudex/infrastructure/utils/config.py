import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BotConfig:
    token: str


@dataclass
class DatabaseConfig:
    host: str
    port: int
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
            data = tomllib.load(f)
        
        return cls(
            bot=BotConfig(**data["bot"]),
            database=DatabaseConfig(**data["database"])
        )
