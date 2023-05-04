from datetime import datetime as dt

from coc import Role as CCRole
from prisma.enums import ClanType as DBClanType
from prisma.enums import Role as DBRole
from prisma.enums import WarFrequency as DBWarFrequency
from prisma.enums import WarResult as DBWarResult
from prisma.enums import WarType as DBWarType
from prisma.models import Member as DBMember


def get_db_role(cc_role: CCRole | None) -> DBRole:
    if cc_role == CCRole.member:
        return DBRole.MEMBER
    elif cc_role == CCRole.elder:
        return DBRole.ELDER
    elif cc_role == CCRole.co_leader:
        return DBRole.CO_LEADER
    elif cc_role == CCRole.leader:
        return DBRole.LEADER
    else:
        raise ValueError(f"Unknown role {cc_role}")


def get_db_clan_type(cc_type: str) -> DBClanType:
    if cc_type == "inviteOnly":
        return DBClanType.INVITE_ONLY
    elif cc_type == "closed":
        return DBClanType.CLOSED
    elif cc_type == "open":
        return DBClanType.OPEN
    else:
        raise ValueError(f"Unknown clan type {cc_type}")


def get_db_war_frequency(cc_frequency: str) -> DBWarFrequency:
    if cc_frequency == "always":
        return DBWarFrequency.ALWAYS
    elif cc_frequency == "moreThanOncePerWeek":
        return DBWarFrequency.MORE_THAN_ONCE_PER_WEEK
    elif cc_frequency == "oncePerWeek":
        return DBWarFrequency.ONCE_PER_WEEK
    elif cc_frequency == "lessThanOncePerWeek":
        return DBWarFrequency.LESS_THAN_ONCE_PER_WEEK
    elif cc_frequency == "never":
        return DBWarFrequency.NEVER
    else:
        raise ValueError(f"Unknown war frequency {cc_frequency}")


def get_db_war_type(cc_type: str | None) -> DBWarType:
    if cc_type == "random":
        return DBWarType.RANDOM
    elif cc_type == "friendly":
        return DBWarType.FRIENDLY
    elif cc_type == "cwl":
        return DBWarType.LEAGUE
    else:
        raise ValueError(f"Unknown war type {cc_type}")


def get_db_war_result(cc_result: str) -> DBWarResult:
    if cc_result == "won":
        return DBWarResult.WIN
    elif cc_result == "lost":
        return DBWarResult.LOSS
    elif cc_result == "tied":
        return DBWarResult.TIE
    elif cc_result in ("winning", "tied", "losing"):
        return DBWarResult.IN_PROGRESS
    else:
        raise ValueError(f"Unknown war result {cc_result}")


def is_member_active(before: DBMember, after: DBMember) -> bool:
    """
    A member is active if:
    - their donations have increased
    - their donations received have increased
    - their attack wins have increased
    - their capital contributions have increased
    - their versus trophies have changed
    - their war stars have increased
    """

    if before.donations < after.donations:
        return True
    elif before.donations_received < after.donations_received:
        return True
    elif before.attack_wins < after.attack_wins:
        return True
    elif before.capital_contributions < after.capital_contributions:
        return True
    elif before.versus_trophies != after.versus_trophies:
        return True
    elif before.war_stars < after.war_stars:
        return True
    else:
        return False
