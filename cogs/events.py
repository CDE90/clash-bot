from datetime import datetime as dt

from discord.ext import commands, tasks
from prisma.models import Member as DBMember

import config
from main import ClashBot
from utils import (
    get_db_clan_type,
    get_db_role,
    get_db_war_frequency,
    get_db_war_result,
    get_db_war_type,
    is_member_active,
)


class EventsCog(commands.Cog):
    def __init__(self, bot: ClashBot):
        self.bot = bot

        self.handle_events.start()

    @tasks.loop(seconds=300)
    async def handle_events(self):
        clan = await self.bot.cc.get_clan(config.CLAN_TAG)

        clan_type = get_db_clan_type(clan.type)
        clan_war_frequency = get_db_war_frequency(clan.war_frequency)
        clan_tag = clan.tag
        clan_name = clan.name or ""
        clan_level = clan.level or 0
        clan_description = clan.description or ""
        clan_points = clan.points or 0
        clan_capital_points = clan.capital_points or 0
        clan_required_trophies = clan.required_trophies or 0
        clan_required_townhall = clan.required_townhall or 0
        clan_war_win_streak = clan.war_win_streak or 0
        clan_war_wins = clan.war_wins or 0
        clan_war_ties = clan.war_ties or 0
        clan_war_losses = clan.war_losses or 0
        clan_member_count = clan.member_count or 0

        db_clan = await self.bot.db.clan.upsert(
            where={"tag": clan.tag},
            data={
                "create": {
                    "tag": clan_tag,
                    "name": clan_name,
                    "level": clan_level,
                    "type": clan_type,
                    "description": clan_description,
                    "points": clan_points,
                    "capital_points": clan_capital_points,
                    "required_trophies": clan_required_trophies,
                    "required_townhall": clan_required_townhall,
                    "war_frequency": clan_war_frequency,
                    "war_win_streak": clan_war_win_streak,
                    "war_wins": clan_war_wins,
                    "war_ties": clan_war_ties,
                    "war_losses": clan_war_losses,
                    "member_count": clan_member_count,
                },
                "update": {
                    "name": clan_name,
                    "level": clan_level,
                    "type": clan_type,
                    "description": clan_description,
                    "points": clan_points,
                    "capital_points": clan_capital_points,
                    "required_trophies": clan_required_trophies,
                    "required_townhall": clan_required_townhall,
                    "war_frequency": clan_war_frequency,
                    "war_win_streak": clan_war_win_streak,
                    "war_wins": clan_war_wins,
                    "war_ties": clan_war_ties,
                    "war_losses": clan_war_losses,
                    "member_count": clan_member_count,
                },
            },
        )

        members = await self.bot.cc.get_members(config.CLAN_TAG)

        current_members: list[DBMember] = []

        for member in members:
            player = await self.bot.cc.get_player(member.tag)

            role = get_db_role(member.role)

            prev_db_member = await self.bot.db.member.find_unique(
                where={"tag": member.tag}
            )

            db_member = await self.bot.db.member.upsert(
                where={"tag": member.tag},
                data={
                    "create": {
                        "tag": member.tag,
                        "name": member.name,
                        "role": role,
                        "trophies": player.trophies,
                        "clan_rank": member.clan_rank,
                        "previous_clan_rank": member.clan_previous_rank,
                        "donations": player.donations,
                        "donations_received": player.received,
                        "clanId": db_clan.id,
                        "versus_trophies": player.versus_trophies,
                        "attack_wins": player.attack_wins,
                        "capital_contributions": player.clan_capital_contributions,
                        "war_stars": player.war_stars,
                    },
                    "update": {
                        "role": role,
                        "trophies": player.trophies,
                        "clan_rank": member.clan_rank,
                        "previous_clan_rank": member.clan_previous_rank,
                        "donations": player.donations,
                        "donations_received": player.received,
                        "versus_trophies": player.versus_trophies,
                        "attack_wins": player.attack_wins,
                        "capital_contributions": player.clan_capital_contributions,
                        "war_stars": player.war_stars,
                    },
                },
            )

            current_members.append(db_member)

            if prev_db_member:
                is_newly_active = is_member_active(prev_db_member, db_member)
            else:
                is_newly_active = True

            if is_newly_active:
                await self.bot.db.member.update(
                    where={"id": db_member.id},
                    data={
                        "last_active": dt.utcnow(),
                        "activity_hits": {"increment": 1},
                    },
                )
            else:
                await self.bot.db.member.update(
                    where={"id": db_member.id},
                    data={"activity_misses": {"increment": 1}},
                )

        all_db_members = await self.bot.db.member.find_many(
            where={"clanId": db_clan.id}
        )

        for db_member in all_db_members:
            current_member = (
                len([member for member in current_members if member.id == db_member.id])
                > 0
            )

            if db_member.current_member != current_member:
                await self.bot.db.member.update(
                    where={"id": db_member.id},
                    data={"current_member": current_member},
                )

        try:
            war = await self.bot.cc.get_current_war(config.CLAN_TAG)
        except:
            print("No war")
            war = None

        if not war:
            try:
                war = await self.bot.cc.get_clan_war(config.CLAN_TAG)
            except:
                print("No war")
                war = None

        if not war:
            try:
                war = await self.bot.cc.get_league_war(config.CLAN_TAG)
            except:
                print("No war")
                war = None

        if war:
            print("Handling war")
            prep_start_time = war.preparation_start_time
            if not prep_start_time:
                prep_start_time = dt.utcnow()
            else:
                prep_start_time = dt.fromisoformat(prep_start_time.raw_time)

            db_war = await self.bot.db.clanwar.upsert(
                where={
                    "clanId_preparation_start_time": {
                        "clanId": db_clan.id,
                        "preparation_start_time": prep_start_time,
                    }
                },
                data={
                    "create": {
                        "clanId": db_clan.id,
                        "opponent_tag": war.opponent.tag if war.opponent else "",
                        "preparation_start_time": prep_start_time,
                        "war_start_time": dt.fromisoformat(
                            war.start_time.raw_time if war.start_time else ""
                        ),
                        "war_end_time": dt.fromisoformat(
                            war.end_time.raw_time if war.end_time else ""
                        ),
                        "team_size": war.team_size,
                        "attacks_per_member": war.attacks_per_member,
                        "result": get_db_war_result(war.status),
                        "type": get_db_war_type(war.type),
                        "members": {
                            "create": [
                                {
                                    "memberId": member.id,
                                }
                                for member in current_members
                                if len([m for m in war.members if m.tag == member.tag])
                                > 0
                            ]
                        },
                    },
                    "update": {
                        "opponent_tag": war.opponent.tag if war.opponent else "",
                        "war_start_time": dt.fromisoformat(
                            war.start_time.raw_time if war.start_time else ""
                        ),
                        "war_end_time": dt.fromisoformat(
                            war.end_time.raw_time if war.end_time else ""
                        ),
                        "team_size": war.team_size,
                        "attacks_per_member": war.attacks_per_member,
                        "result": get_db_war_result(war.status),
                        "type": get_db_war_type(war.type),
                    },
                },
            )

            db_war_attacks = await self.bot.db.warattack.find_many(
                where={"warId": db_war.id}
            )

            new_attacks = [
                attack
                for attack in war.attacks
                if len(
                    [
                        db_attack
                        for db_attack in db_war_attacks
                        if db_attack.attacker_tag == attack.attacker_tag
                        and db_attack.defender_tag == attack.defender_tag
                    ]
                )
                == 0
            ]

            for attack in new_attacks:
                attacker_member = [
                    member
                    for member in current_members
                    if member.tag == attack.attacker_tag
                ]

                if len(attacker_member) > 0:
                    await self.bot.db.warattack.create(
                        {
                            "attacker_tag": attack.attacker_tag,
                            "defender_tag": attack.defender_tag,
                            "stars": attack.stars,
                            "destruction_percentage": attack.destruction,
                            "duration": attack.duration,
                            "order": attack.order,
                            "warId": db_war.id,
                            "attackerId": attacker_member[0].id,
                        }
                    )

    @handle_events.before_loop
    async def before_handle_events(self):
        await self.bot.wait_until_ready()


async def setup(bot: ClashBot):
    await bot.add_cog(EventsCog(bot))
