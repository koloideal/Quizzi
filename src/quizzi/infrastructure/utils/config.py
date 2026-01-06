import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Self


@dataclass
class BotConfig:
    token: str
    creator_id: int


@dataclass
class SecurityConfig:
    encode_key: str
    encoded_string_length: int = 8


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
class Config:
    bot: BotConfig
    database: DatabaseConfig
    security: SecurityConfig
    
    @classmethod
    def from_toml(cls, path: str | Path) -> Self:
        with open(path, "rb") as f:
            data: dict[str, dict[str, str | int]] = tomllib.load(f)
        
        bot_data: dict[str, str | int] = data["bot"]
        db_data: dict[str, str | int] = data["database"]
        security_data: dict[str, str | int] = data["security"]
        
        return cls(
            bot=BotConfig(
                token=str(bot_data["token"]),
                creator_id=int(bot_data["creator_id"])
            ),
            database=DatabaseConfig(
                host=str(db_data["host"]),
                port=db_data["port"],
                user=str(db_data["user"]),
                password=str(db_data["password"]),
                database=str(db_data["database"])
            ),
            security=SecurityConfig(
                encode_key=str(security_data["encode_key"]),
                encoded_string_length=int(security_data.get("encoded_string_length", 8))
            )
        )
