import asyncio
import logging

from aiogram import Bot, Dispatcher

from trudex.infrastructure.utils.config import Config


async def main():
    logging.basicConfig(level=logging.INFO)
    
    config = Config.from_toml("config.toml")
    
    logging.info("Бот запущен")


if __name__ == "__main__":
    asyncio.run(main())
