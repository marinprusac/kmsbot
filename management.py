import random

from discord import Role, Guild, TextChannel, CategoryChannel, Embed, Member

import tools
from tools import Player

from datahandler import DataHandler

import helper


class DiscordServer:
    admin_role: Role
    alive_role: Role
    dead_role: Role
    registered_role: Role

    announcements_channel: TextChannel
    private_category: CategoryChannel

    guild: Guild

    def __init__(self, guild: Guild):
        self.guild = guild

        announcement_id = 1179035409209106432
        private_category_id = 1179176894239875113

        temp = helper.get_role(guild, 'registered'), helper.get_role(guild, 'dead'), \
               helper.get_role(guild, 'alive'), helper.get_role(guild, 'admin'), \
               helper.get_channel(guild, announcement_id), helper.get_category(guild, private_category_id)

        if any(role is None for role in temp):
            raise BaseException()

        self.registered_role, self.dead_role, self.alive_role, self.admin_role, \
        self.announcements_channel, self.private_category = temp

    async def mission_accomplished(self, killer_id: int) -> bool:

        killed_player: Player | None = None

        players: list[Player] = helper.get_players_from_data(DataHandler.get("players"))
        new_players: list[Player] = []

        killer_player: Player | None = None

        for p in players:
            if p.id == killer_id:
                killer_player = p
                break

        if killer_player is None:
            return False

        for p in players:
            if p.id == killer_player.mission.target:
                killed_player = p
            elif p.id != killer_player.id:
                new_players.append(p)

        if killed_player is None:
            await self.refresh()
            return False

        for member in self.alive_role.members:
            if member.id == killed_player.id:
                await member.remove_roles(self.alive_role)
                await member.add_roles(self.dead_role)
                await self.notify_of_death(member, killer_player)
                break

        if killed_player is not None and killed_player.mission.target != killer_player.id:
            killer_player.mission = killed_player.mission
        elif len(players) <= 2:
            killer_player.mission = None

        new_players.append(killer_player)
        await self.notify_of_new_mission(killer_player)
        DataHandler.set("players", helper.set_data_from_players(new_players))

        await self.refresh()
        return True

    async def reroll_mission(self, player_id: int, reroll_person: bool = False, reroll_location: bool = False, reroll_weapon: bool = False):
        players: list[Player] = helper.get_players_from_data(DataHandler.get('players'))
        new_players: list[Player] = []
        rerolling_player: Player | None = None
        for p in players:
            if p.id == player_id:
                rerolling_player = p
            else:
                new_players.append(p)
        if not rerolling_player.reroll or reroll_person and len(players) <= 2:
            return False
        if reroll_location:
            locations: list[str] = DataHandler.get('locations')
            l_restrictions: set[tuple] = set()
            l_restrictions.add((0,rerolling_player.mission.location))
            delegation = tools.delegation_algorithm({0}, set(locations), set(), l_restrictions)
            rerolling_player.mission.location = list(delegation)[0][1]
        if reroll_weapon:
            weapons: list[str] = DataHandler.get('weapons')
            w_restrictions: set[tuple] = set()
            w_restrictions.add((0, rerolling_player.mission.weapon))
            delegation = tools.delegation_algorithm({0}, set(weapons), set(), w_restrictions)
            rerolling_player.mission.weapon = list(delegation)[0][1]
        if reroll_person:
            not_targeted, targeted_once, targeted_twice = helper.categorize_by_n_of_targets(players)
            restrictions: set[tuple[int, int]] = {(player_id, player_id), (player_id, rerolling_player.mission.target)}
            if len(players) >= 4:
                for p in players:
                    if p.mission is not None and p.mission.target == player_id:
                        restrictions.add((player_id, p.id))
            mission = tools.delegation_algorithm({player_id}, set(map(lambda pl: pl.id, not_targeted)), set(map(lambda pl: pl.id, targeted_once)), restrictions)
            rerolling_player.mission.target = list(mission)[0][1]
        rerolling_player.reroll = False
        new_players.append(rerolling_player)
        DataHandler.set('players', helper.set_data_from_players(new_players))
        await self.notify_of_new_mission(rerolling_player)
        await self.refresh()
        return True

    async def notify_of_death(self, member: Member, killer: Player | None = None):
        channel = helper.get_channel_by_name(self.guild, str(member.id))
        if channel is None:
            return
        if killer is None:
            await channel.send(f"You've been killed by **{self.guild.me.name}**. Spooky")
            return
        await channel.send(f"You've been killed by **{helper.get_member(self.guild, id=killer.id).name}**. Spooky")

    async def notify_of_new_mission(self, player: Player):
        channel = helper.get_channel_by_name(self.guild, str(player.id))
        if channel is None:
            return
        if player.mission is None:
            await channel.send("**You have no more targets to kill!**")
            return
        target: Member | None = helper.get_member(self.guild, id=player.mission.target)
        if target is None:
            return

        embed = Embed(title="Assassination Mission",
                              description="This is a mission assigned uniquely to you. Kill the target at the specified location and with the specified weapon. Don't get seen.",
                              color=0xFF0000)
        embed.add_field(name="Target", value=f"Your target is the person named **{target.name}**.",
                        inline=False)

        embed.add_field(name="Location", value=f"You must murder your target at: **{player.mission.location}**.", inline=True)
        embed.add_field(name="Weapon", value=f"Use **{player.mission.weapon}** to murder them!", inline=True)

        footer_text = ''
        if player.reroll:
            footer_text = 'You have an available re-roll. Use it wisely!'
        else:
            footer_text = 'You currently have no available re-rolls.'

        embed.set_footer(text=footer_text)
        await channel.send(embed=embed)

    async def clean_up_illegal_roles(self):
        game_running = DataHandler.get('running')
        if game_running:
            for member in self.registered_role.members:
                await member.remove_roles(self.registered_role)
        else:
            for member in self.alive_role.members:
                await member.remove_roles(self.alive_role)
            for member in self.dead_role.members:
                await member.remove_roles(self.dead_role)

    async def update_missions(self):
        previous_players: list[tools.Player] = helper.get_players_from_data(DataHandler.get('players'))
        alive_players: list[Player] = [Player(member.id) for member in self.alive_role.members]

        stay_players: list[Player] = []
        remove_players: list[Player] = []

        # extract players that stayed and players that got removed
        for p1 in previous_players:
            present = False
            for p2 in alive_players:
                if p2.id == p1.id:
                    p2.alive = p1.alive
                    p2.reroll = p1.reroll
                    p2.mission = p1.mission
                    stay_players.append(p1)
                    present = True
                    break
            if not present:
                remove_players.append(p1)

        # remove missions targeting removed players
        for ps in stay_players:
            for pr in remove_players:
                if ps.mission is not None and ps.mission.target == pr.id:
                    ps.mission = None
                    break

        # check if there are enough players
        if len(alive_players) <= 1:
            dictps = []
            for p in alive_players:
                if p.mission is not None:
                    p.mission = None
                    await self.notify_of_new_mission(p)
                dictps.append(helper.player_to_dict(p))
            DataHandler.set("players", dictps)
            return

        # prepare data for generating new missions
        missing_mission: set[int] = set()
        un_targeted: set[int] = set()
        targeted: set[int] = set()
        restrictions: set[tuple[int, int]] = set()

        for p1 in alive_players:
            restrictions.add((p1.id, p1.id))

            if p1.mission is None:
                missing_mission.add(p1.id)
            elif len(alive_players) > 3:
                restrictions.add((p1.mission.target, p1.id))

            targeted_count = 0

            has_mission = False

            for p2 in alive_players:
                if p1.mission is not None and p1.mission.target == p2.id:
                    has_mission = True
                if p2.mission and p2.mission.target == p1.id:
                    targeted_count += 1
                    break

            if not has_mission:
                p1.mission = None
                missing_mission.add(p1.id)

            if targeted_count == 1:
                targeted.add(p1.id)
            elif targeted_count == 0:
                un_targeted.add(p1.id)

        # delegate new missions
        new_targets = tools.delegation_algorithm(missing_mission, un_targeted,
                                                 targeted, restrictions)
        locations: list[str] = DataHandler.get("locations")
        weapons: list[str] = DataHandler.get("weapons")

        for m in new_targets:
            loc = random.choice(locations)
            wpn = random.choice(weapons)
            for p1 in alive_players:
                if p1.id == m[0]:
                    p1.mission = tools.Mission(m[1], loc, wpn)
                    await self.notify_of_new_mission(player=p1)

        DataHandler.set("players", helper.set_data_from_players(alive_players))

    async def refresh(self):
        await self.clean_up_illegal_roles()
        await self.update_missions()