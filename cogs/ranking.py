from enum import Enum
from typing import Callable

import discord
from discord.ext import commands
from prisma.models import Member

from main import ClashBot


class SortBy(Enum):
    WarStars = "war_stars"
    WarAttacks = "war_attacks"
    AttackWins = "attack_wins"
    ActivityRatio = "activity_ratio"
    LastActive = "last_active"
    Donations = "donations"
    Trophies = "trophies"


class Ranking(commands.Cog):
    def __init__(self, bot: ClashBot):
        self.bot = bot

    @commands.command()
    async def war(self, ctx: commands.Context, size: int, *, sort_by: str = "all"):
        """A command which returns a reccomended list of players for the next war"""

        members = await self.bot.db.member.find_many(
            where={"current_member": True},
            include={"WarAttack": True},
        )

        if sort_by == "all":
            options = [(sortable, 1) for sortable in SortBy]
        else:
            # each option can either be `option` or `option:weight` each option is seperated by a comma
            # e.g. `war_stars:2,attack_wins,activity_ratio:0.5`
            # if no weight is specified, it defaults to 1

            options = [
                (
                    SortBy(option.split(":")[0].strip().lower()),
                    float(option.split(":")[1].strip()),
                )
                if ":" in option
                else (SortBy(option.strip().lower()), 1)
                for option in sort_by.split(",")
            ]

        member_scores: dict[str, float] = {}

        def get_scores(
            members: list[Member],
            func: Callable[[Member], int | float],
            /,
            reverse: bool,
            weight: float,
        ) -> None:
            scores = {member.tag: func(member) for member in members}

            sorted_members = sorted(scores.items(), key=lambda x: x[1], reverse=reverse)

            for index, (tag, _) in enumerate(sorted_members):
                member_scores[tag] = member_scores.get(tag, 0) + (index * weight)

        selected_options = [option for option, _ in options]

        def get_weight(option: SortBy) -> float:
            return next((weight for opt, weight in options if opt == option), 1)

        if SortBy.WarStars in selected_options:
            get_scores(
                members,
                lambda member: sum(attack.stars for attack in member.WarAttack or []),
                reverse=False,
                weight=get_weight(SortBy.WarStars),
            )

        if SortBy.WarAttacks in selected_options:
            get_scores(
                members,
                lambda member: len(member.WarAttack or []),
                reverse=False,
                weight=get_weight(SortBy.WarAttacks),
            )

        if SortBy.AttackWins in selected_options:
            get_scores(
                members,
                lambda member: member.attack_wins,
                reverse=False,
                weight=get_weight(SortBy.AttackWins),
            )

        if SortBy.ActivityRatio in selected_options:
            get_scores(
                members,
                lambda member: member.activity_hits
                / (member.activity_hits + member.activity_misses),
                reverse=False,
                weight=get_weight(SortBy.ActivityRatio),
            )

        if SortBy.LastActive in selected_options:
            get_scores(
                members,
                lambda member: (ctx.message.created_at - member.last_active).seconds
                / 3600,
                reverse=True,
                weight=get_weight(SortBy.LastActive),
            )

        if SortBy.Donations in selected_options:
            get_scores(
                members,
                lambda member: member.donations - member.donations_received,
                reverse=False,
                weight=get_weight(SortBy.Donations),
            )

        if SortBy.Trophies in selected_options:
            get_scores(
                members,
                lambda member: member.trophies,
                reverse=False,
                weight=get_weight(SortBy.Trophies),
            )

        sorted_members = sorted(member_scores.items(), key=lambda x: x[1], reverse=True)

        await ctx.send(
            embed=discord.Embed(
                title=f"Top {size} players for next war",
                description="\n".join(
                    f"**{index + 1}.** {next((member.name for member in members if member.tag == tag), tag)} - {score}"
                    for index, (tag, score) in enumerate(sorted_members[:size])
                ),
            )
        )


async def setup(bot: ClashBot):
    await bot.add_cog(Ranking(bot))
