import asyncio
import os

import coc
import discord
from discord.ext import commands
from prisma import Prisma

import config
from utils.logger import setup_logging


class ClashBot(commands.Bot):
    def __init__(
        self, db: Prisma, cc: coc.Client, cec: coc.EventsClient, *args, **kwargs
    ):
        self.db = db
        self.cc = cc
        self.cec = cec

        super().__init__(*args, **kwargs)

    async def setup_hook(self):
        await self.db.connect()
        await self.cc.login(config.API_EMAIL, config.API_PASS)
        await self.cec.login(config.API_EMAIL, config.API_PASS)

        self.cec.add_clan_updates(config.CLAN_TAG)

        self.cec.add_player_updates(
            *[m.tag for m in await self.cc.get_members(config.CLAN_TAG)]
        )

        return await super().setup_hook()

    async def on_ready(self):
        if not self.user:
            return

        print(f"Logged in as {self.user.name} ({self.user.id})")


setup_logging()


db = Prisma()

cc = coc.Client()
cec = coc.EventsClient()

intents = discord.Intents.all()

bot = ClashBot(
    db,
    cc,
    cec,
    command_prefix="!",
    description="Clash of Clans bot",
    intents=intents,
)

# @coc.ClanEvents.member_donations()


async def main():
    async with bot:
        for filename in os.listdir("cogs"):
            if filename.endswith(".py"):
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"Loaded cogs.{filename[:-3]}")

        await bot.load_extension("jishaku")

        await bot.start(config.BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
