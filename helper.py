from discord import Guild, Member, Role, TextChannel, CategoryChannel
from discord.ext.commands import Context
from datahandler import Player, Mission, KillLog


def get_alive_players(players: list[Player]) -> list[Player]:
    return [p for p in players if p.is_alive]


def get_player_channel(guild: Guild, player: Player) -> TextChannel:
    return get_channel_by_name(guild, str(player.id))


def get_member_from_player(guild: Guild, player: Player) -> Member:
    memb = guild.get_member(player.id)
    if memb is None:
        raise AttributeError
    return memb


def get_player(id: int, players: list[Player]) -> Player:
    for p in players:
        if p.id == id:
            return p
    raise AttributeError


def get_kill_count(player: Player, kill_logs: list[KillLog]) -> int:
    kill_count: int = 0
    for kill_log in kill_logs:
        if kill_log.killer_id == player.id:
            kill_count += 1
    return kill_count


def categorize_by_n_of_targets(players: list[Player]) -> tuple[list[Player], list[Player], list[Player]]:
    no: list[Player] = []
    one: list[Player] = []
    two: list[Player] = []

    for p in players:
        count = 0
        for p2 in players:
            if p2.mission is not None and p2.mission.target_id == p.id:
                count += 1
        if count == 0:
            no.append(p)
        elif count == 1:
            one.append(p)
        else:
            two.append(p)
    return no, one, two



def extract_members_from_args(ctx: Context, *mentions: str) -> list[Member]:
    guild = ctx.guild
    if guild is None:
        raise AttributeError

    members: list[Member] = []
    if len(mentions) == 0:
        member = get_member(guild, id=ctx.author.id)
        members.append(member)

    for mention in mentions:
        member = get_member_from_mention(guild, mention)
        members.append(member)
    return members


def get_member(guild: Guild, name: str | None = None,
               id: int | None = None) -> Member:
    if name is not None:
        memb = guild.get_member_named(name)
        if memb is None:
            raise AttributeError
        return memb

    if id is not None:
        memb = guild.get_member(id)
        if memb is None:
            raise AttributeError
        return memb
    raise AttributeError


def get_member_from_mention(guild: Guild, mention: str) -> Member:
    if mention.startswith('<@') and mention.endswith('>'):
        mention = mention.strip('<@!>')
        return guild.get_member(int(mention))
    raise AttributeError


def get_role(guild: Guild, name: str | None = None, id: int | None = None) -> Role:
    if guild is None:
        raise AttributeError
    if name is not None:
        for r in guild.roles:
            if r.name == name:
                return r
        raise AttributeError

    if id is not None:
        role = guild.get_role(id)
        if role is None:
            raise AttributeError
        return role
    raise AttributeError


def get_channel(guild: Guild, channel_id: int) -> TextChannel:
    channel = guild.get_channel(channel_id)
    if channel is None:
        raise AttributeError
    return channel


def get_channel_by_name(guild: Guild, name: str) -> TextChannel:
    channels = guild.text_channels
    for c in channels:
        if c.name == name:
            return c
    raise AttributeError


def get_category(guild: Guild, id: int) -> CategoryChannel:
    for c in guild.categories:
        if c.id == id:
            return c
    raise AttributeError