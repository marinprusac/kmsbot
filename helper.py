from discord import Guild, Member, Role, TextChannel, CategoryChannel
from discord.ext.commands import Context
from tools import Player, Mission


def categorize_by_n_of_targets(players: list[Player]) -> tuple[set[Player], set[Player], set[Player]]:
    no: set[Player] = set()
    one: set[Player] = set()
    two: set[Player] = set()

    for p in players:
        count = 0
        for p2 in players:
            if p2.mission is not None and p2.mission.target == p.id:
                count += 1
        if count == 0:
            no.add(p)
        elif count == 1:
            one.add(p)
        else:
            two.add(p)
    return no, one, two


def dict_to_player(d: dict) -> Player:
    p = Player(d["id"])
    p.alive = d["alive"]
    p.reroll = d["reroll"]
    if "mission" in d:
        p.mission = Mission(d["mission"]["target"], d["mission"]["location"], d["mission"]["weapon"])
    else:
        p.mission = None
    return p


def player_to_dict(p: Player) -> dict:
    d = dict()
    d["id"] = p.id
    d["alive"] = p.alive
    d["reroll"] = p.reroll
    if p.mission is not None:
        d["mission"] = dict()
        d["mission"]["target"] = p.mission.target
        d["mission"]["location"] = p.mission.location
        d["mission"]["weapon"] = p.mission.weapon
    return d


def get_players_from_data(data: list[dict]) -> list[Player]:
    return [dict_to_player(d) for d in data]


def set_data_from_players(players: list[Player]) -> list[dict]:
    return [player_to_dict(p) for p in players]


# helper functions
def extract_members_from_args(ctx: Context,
                              *mentions: str) -> list[Member] | None:
    guild = ctx.guild
    if guild is None:
        return None

    members: list[Member] = []
    if len(mentions) == 0:
        member = get_member(guild, id=ctx.author.id)
        if member is None:
            return None
        members.append(member)

    for mention in mentions:
        member = get_member_from_mention(guild, mention)
        if member is None or member.bot:
            return None
        members.append(member)
    return members


def get_member(guild: Guild, name: str | None = None,
               id: int | None = None) -> Member | None:
    if name is not None:
        memb = guild.get_member_named(name)
        return memb

    if id is not None:
        memb = guild.get_member(id)
        return memb


def get_member_from_mention(guild: Guild, mention: str) -> Member | None:
    if mention.startswith('<@') and mention.endswith('>'):
        mention = mention.strip('<@!>')
        return guild.get_member(int(mention))
    return None


def get_role(guild: Guild, name: str | None = None,
             id: int | None = None) -> Role | None:
    if guild is None:
        return None
    if name is not None:
        for r in guild.roles:
            if r.name == name:
                return r
        return None

    if id is not None:
        return guild.get_role(id)


def get_channel(guild: Guild, channel_id: int) -> TextChannel | None:
    return guild.get_channel(channel_id)


def get_channel_by_name(guild: Guild, name: str) -> TextChannel | None:
    channels = guild.text_channels
    for c in channels:
        if c.name == name:
            return c
    return None


def get_category(guild: Guild, id: int) -> CategoryChannel | None:
    for c in guild.categories:
        if c.id == id:
            return c
    return None