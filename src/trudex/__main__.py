import asyncio
import logging

from aiogram import Bot, Dispatcher

from trudex.infrastructure.utils.config import AppConfig


async def main():
    logging.basicConfig(level=logging.INFO)
    
    config = AppConfig.from_toml()
    
    logging.info("Бот запущен")


if __name__ == "__main__":
    asyncio.run(main())
