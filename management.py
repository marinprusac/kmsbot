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
    everyone_role: Role

    announcements_channel: TextChannel
    private_category: CategoryChannel

    guild: Guild

    def __init__(self, guild: Guild):
        self.guild = guild

        announcement_id = 1179035409209106432
        private_category_id = 1179176894239875113

        temp = helper.get_role(guild, '@everyone'), helper.get_role(guild, 'registered'), helper.get_role(guild, 'dead'), \
               helper.get_role(guild, 'alive'), helper.get_role(guild, 'admin'), \
               helper.get_channel(guild, announcement_id), helper.get_category(guild, private_category_id)

        if any(role is None for role in temp):
            raise BaseException()

        self.everyone_role, self.registered_role, self.dead_role, self.alive_role, self.admin_role, \
        self.announcements_channel, self.private_category = temp

    async def final(self):
        day_count: int = DataHandler.get('day')
        kill_data: list[dict] = DataHandler.get('daykills')
        last_day: dict | None = None
        players: list[Player] = helper.get_players_from_data(DataHandler.get('players'))

        for day in kill_data:
            if day['day'] == day_count:
                last_day = day
                break

        if last_day is None:
            return False

        kills: list[dict] = last_day['kills']

        if len(kills) == 0:
            players = helper.get_players_from_data(DataHandler.get('players'))
            for p in players:
                if not p.reroll:
                    p.reroll = True
                    await self.notify_of_new_mission(p)
            DataHandler.set('players', helper.set_data_from_players(players))

        title = f"## Day {day_count} and FINAL Report\nDear {self.everyone_role.mention},"
        first_part = "In the last 24 hours, there have been **0** kills. A pity."
        second_part = "However, the time is up and the game must end!"
        third_part = ""
        signature = "*THE EVIL GM*"

        if len(kills) == 1:
            first_part = f"In the last 24 hours, there has been **1** kill."
        elif len(kills) > 1:
            first_part = f"In the last 24 hours, there have been {len(kills)} kills."

        if len(kills) > 0:
            second_part = '### Kill list\n'
            for kill in kills:
                target = helper.get_member(self.guild, id=kill['target'])
                killer = helper.get_member(self.guild, id=kill['killer'])
                second_part += f"**{target.name}** has been killed by **{killer.name}**.\n"

        if len(self.alive_role.members) == 1:
            third_part = f"**{self.alive_role.members[0].name}, being the sole survivor, is victorious!**\nYou have the honor to be my personal murder target! :smiling_imp: \n**MUAHAHAHAHAHAHA**\n"
        else:
            survivors: list[Player] = [helper.get_player(member.id, players) for member in self.alive_role.members ]
            max_kills: int = -1
            winners: list[Player] = []
            losers: list[Player] = []

            third_part = "It seems to me that we have multiple survivors...\n"
            third_part += "### Let's see how they compare:\n"

            for survivor in survivors:
                kill_count = helper.get_kill_count(survivor, kill_data)
                max_kills = max(max_kills, kill_count)
                third_part += f"Number of {helper.get_member(self.guild, id=survivor.id).name}'s kills is {kill_count}.\n"

            for survivor in survivors:
                if helper.get_kill_count(survivor, kill_data) < max_kills:
                    losers.append(survivor)
                else:
                    winners.append(survivor)
            third_part += "\n"

            if len(losers) == 1:
                third_part += "Let's get rid of this coward with a low kill count:\n"
                third_part += f"***{helper.get_member(self.guild, id=losers[0].id).name}* has been brutally murdered by the *Evil GM***.\n"
            elif len(losers) > 1:
                third_part += "Let's get rid of these cowards with low kill counts:\n"
                for loser in losers:
                    third_part += f"***{helper.get_member(self.guild, id=loser.id).name}* has been brutally murdered by the **Evil GM***.\n"
            third_part += "\n"

            if len(winners) == 1:
                third_part += f"**This leaves us with only one winner. And that is {helper.get_member(self.guild, id=winners[0].id).name}**.\n"
                third_part += f"You have the honor to be my personal murder target! :smiling_imp: \n**MUAHAHAHAHAHAHA**\n"
            elif len(winners) > 1:
                if len(losers) == 0:
                    third_part += "With everyone being equally as good. I declare you all winners! But most importantly...\n"
                else:
                    third_part += f"Now there are only {len(winners)} players left:\n"
                    for winner in winners:
                        third_part += f"{helper.get_member(self.guild, id=winner.id).name}\n"
                    third_part += "I declare you all winners! But most importantly...\n"

                third_part += f"You have the honor to be my personal murder targets! :smiling_imp: \n**MUAHAHAHAHAHAHA**\n"

        await self.announcements_channel.send(f'{title}\n{first_part}\n{second_part}\n{third_part}\n\n{signature}')

        kill_data.append({'day': day_count+1, 'kills': []})
        DataHandler.set('day', day_count+1)
        return True

    async def next_day(self):
        day_count: int = DataHandler.get('day')
        days_dict: list[dict] = DataHandler.get('daykills')
        last_day: dict | None = None

        for day in days_dict:
            if day['day'] == day_count:
                last_day = day
                break

        if last_day is None:
            return False

        kills: list[dict] = last_day['kills']

        if len(kills) == 0:
            players = helper.get_players_from_data(DataHandler.get('players'))
            for p in players:
                if not p.reroll:
                    p.reroll = True
                    await self.notify_of_new_mission(p)
            DataHandler.set('players', helper.set_data_from_players(players))

        title = f"## Day {day_count} Report\nDear {self.everyone_role.mention},"
        first_part = "In the last 24 hours, there have been **0** kills. A pity."
        second_part = "In order to bring up the action I decided to give y'all a **free mission re-roll**."
        third_part = "Don't disappoint me again!"
        signature = "*THE EVIL GM*"

        if len(kills) == 1:
            first_part = f"In the last 24 hours, there has been **1** kill."
        elif len(kills) > 1:
            first_part = f"In the last 24 hours, there have been {len(kills)} kills."

        if len(kills) > 0:
            second_part = '### Kill list\n'
            for kill in kills:
                target = helper.get_member(self.guild, id=kill['target'])
                killer = helper.get_member(self.guild, id=kill['killer'])
                second_part += f"**{target.name}** has been killed by **{killer.name}**.\n"

            if len(self.alive_role.members) == 1:
                title = f"## Day {day_count} and FINAL Report\nDear {self.everyone_role.mention},"
                third_part = f"**{self.alive_role.members[0].name}, being the sole survivor, is victorious!**\nYou have the honor to be my personal murder target! :smiling_imp: \n**MUAHAHAHAHAHAHA**\n"
            else:
                third_part = "Keep it going and you shall be rewarded graciously..."

        await self.announcements_channel.send(f'{title}\n{first_part}\n{second_part}\n{third_part}\n\n{signature}')

        days_dict.append({'day': day_count+1, 'kills': []})
        DataHandler.set('day', day_count+1)
        return True

    async def mission_accomplished(self, killer_id: int) -> bool:

        players: list[Player] = helper.get_players_from_data(DataHandler.get("players"))
        new_players: list[Player] = players.copy()

        killer_player: Player | None = helper.get_player(killer_id, players)

        if killer_player is None or killer_player.mission is None:
            return False

        killed_player: Player | None = helper.get_player(killer_player.mission.target, players)

        if killed_player is None:
            return False

        self.record_kill(killer_player, killed_player)

        killed_member = helper.get_member(self.guild, id=killed_player.id)
        if killed_member is None:
            return False

        await killed_member.remove_roles(self.alive_role)
        await killed_member.add_roles(self.dead_role)
        await self.notify_of_death(killed_member, killer_player)

        if killed_player is not None and killed_player.mission.target != killer_player.id:
            killer_player.mission = killed_player.mission
            killed_player.reroll = True
        elif len(players) <= 2:
            killer_player.mission = None

        new_players.append(killer_player)
        new_players.remove(killed_player)

        DataHandler.set("players", helper.set_data_from_players(new_players))

        await self.notify_of_new_mission(killer_player)
        await self.refresh()
        return True

    def record_kill(self, killer: Player, target: Player) -> bool:
        day_count: int = DataHandler.get("day")
        day_dict: list[dict] = DataHandler.get("daykills")
        new_day_dict: list[dict] = []

        current_day: dict | None = None
        for day in day_dict:
            if day["day"] == day_count:
                current_day = day
            else:
                new_day_dict.append(day)
        if current_day is None:
            return False

        current_day["kills"].append({"killer": killer.id, "target": target.id})
        new_day_dict.append(current_day)

        DataHandler.set('daykills', new_day_dict)
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