import discord
from discord.ext import commands

from main import ClashBot


class Test(commands.Cog):
    def __init__(self, bot: ClashBot):
        self.bot = bot

    @commands.command()
    async def test(self, ctx: commands.Context):
        await ctx.send("Test command")


async def setup(bot: ClashBot):
    await bot.add_cog(Test(bot))
