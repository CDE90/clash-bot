import asyncio
import os

import coc
import discord
from discord.ext import commands

import config
from prisma import Prisma
from utils.logger import setup_logging


class ClashBot(commands.Bot):
    def __init__(self, db: Prisma, cc: coc.Client, *args, **kwargs):
        self.db = db
        self.cc = cc

        super().__init__(*args, **kwargs)

    async def setup_hook(self):
        await self.db.connect()
        await self.cc.login(config.API_EMAIL, config.API_PASS)

        return await super().setup_hook()

    async def on_ready(self):
        if not self.user:
            return

        print(f"Logged in as {self.user.name} ({self.user.id})")


setup_logging()


db = Prisma()

cc = coc.Client(cache_max_size=None, key_names=config.KEY_ENVIRONMENT)  # type: ignore

intents = discord.Intents.all()

bot = ClashBot(
    db,
    cc,
    command_prefix="!",
    description="Clash of Clans bot",
    intents=intents,
)


async def main():
    async with bot:
        for filename in os.listdir("cogs"):
            if filename.endswith(".py"):
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"Loaded cogs.{filename[:-3]}")

        await bot.load_extension("jishaku")

        await bot.start(config.BOT_TOKEN)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
