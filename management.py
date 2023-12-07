import random
from discord.ext import commands
from discord import Role, Guild, TextChannel, CategoryChannel, Embed, Member
import tools
from datahandler import AllData, Player, Mission, KillLog
import helper


class DiscordServer:
	admin_role: Role
	alive_role: Role
	dead_role: Role
	registered_role: Role
	everyone_role: Role

	announcements_channel: TextChannel
	admin_channel: TextChannel
	private_category: CategoryChannel

	guild: Guild
	data: AllData

	def __init__(self, guild: Guild):
		self.guild = guild

		announcement_id = 1179035409209106432
		admin_channel_id = 0
		private_category_id = 1179176894239875113

		temp = helper.get_role(guild, '@everyone'), helper.get_role(guild, 'registered'), \
		       helper.get_role(guild, 'dead'), helper.get_role(guild, 'alive'), helper.get_role(guild, 'admin'), \
		       helper.get_channel(guild, announcement_id), helper.get_channel(guild, admin_channel_id),\
		       helper.get_category(guild, private_category_id)

		if any(role is None for role in temp):
			raise BaseException()

		self.everyone_role, self.registered_role, self.dead_role, self.alive_role, self.admin_role, \
		self.announcements_channel, self.admin_channel, self.private_category = temp
		self.data = AllData(guild.id)

	async def start_game(self):

		# check if the conditions are met
		if self.data.game_running:
			await self.admin_channel.send("Command failed. Game is already running!")
			return
		if len(self.registered_role.members) <= 1:
			await self.admin_channel.send("There aren't enough players! :(")
			return
		if len(self.data.locations) < 1:
			await self.admin_channel.send("There aren't enough locations! :(")
			return
		if len(self.data.weapons) < 1:
			await self.admin_channel.send("There aren't enough weapons! :(")
			return

		# add all registered players to the game
		for member in self.registered_role.members.copy():
			await self.add_player(member, False)

		# announce game start to everyone
		announce_text = "# Game Started\n"
		announce_text += "The Game of *KILLING ME SOFTLY* has officially started.\n"
		announce_text += "Everyone has a mission: kill the target at a specified location, with a specified weapon.\n"
		announce_text += "Don't get killed yourself and survive to see yourself win the game with the most kills.\n"
		announce_text += "The winner will be rewarded handsomely... hehehe.\n\n"
		announce_text += "*THE EVIL GM*"
		await self.announcements_channel.send(announce_text)

		# set initial missions
		await self.set_initial_missions()

		# finalize data and return
		self.data.game_running = True
		self.data.day_number = 1
		self.data.save()
		await self.admin_channel.send("Game started!")

	async def end_game(self):
		if not self.data.game_running:
			await self.admin_channel.send("Command failed. Reason: Game isn't running!")
			return

		for player in self.data.players.copy():
			await self.remove_player(player, False)

		self.data.game_running = False
		self.data.players = []
		self.data.kill_logs = []
		self.data.day_number = 0
		self.data.save()
		await self.admin_channel.send("Game ended!")

	async def add_player(self, member: Member, special: bool = True):
		players = self.data.players

		if not self.data.game_running:
			await self.admin_channel.send("Game isn't running")
			return

		# add player to the list
		player = Player(member.id)
		players.append(player)

		# remove registration and mark as alive
		await member.remove_roles(self.registered_role)
		await member.add_roles(self.alive_role)

		# create private channel
		tc = await self.private_category.create_text_channel(str(member.id))
		for i in range(5):
			await tc.set_permissions(member, view_channel=True)  # repeating because sometimes it doesn't work

		# if the adding was special, it means that the player was added in the middle of the game
		if special:
			mission = self.get_new_mission(player)
			await self.assign_mission(player, mission, True)
			await self.announcements_channel.send(f"{self.everyone_role},"
			                                      f"**{member.name}** has been added to the game, watch out!")

		self.data.save()

	async def remove_player(self, player: Player, special: bool = True):
		member = helper.get_member_from_player(self.guild, player)

		self.data.players.remove(player)

		# remove game-related roles
		await member.remove_roles(self.alive_role, self.dead_role)

		# delete private channel
		await helper.get_player_channel(self.guild, player).delete()

		# if removal was special, announce the removal and refresh missions
		if special:
			for other_player in self.data.players:
				if other_player.mission and other_player.mission.target_id == player.id:
					mission = self.get_new_mission(other_player)
					await self.assign_mission(other_player, mission, False)
			await self.announcements_channel.send(f"{self.everyone_role},"
			                                      f"**{member.name}** has been removed fom the game, phew.")

		self.data.save()

	async def day_report(self, final: bool = False):
		self.data.load()

		day_count: int = self.data.day_number
		kill_logs: list[KillLog] = self.data.kill_logs
		last_day: list[KillLog] = list(filter(lambda log: log.day_number == day_count, kill_logs))
		players: list[Player] = self.data.players
		alive_players: list[Player] = list(filter(lambda p: p.is_alive, players))
		final = final or len(alive_players) == 1

		# if there were no kills last night, grant rerolls
		if len(last_day) == 0:
			for p in players:
				if not p.has_reroll:
					await self.assign_mission(p, p.mission, True)
			self.data.save()

		# message constructing
		title = greeting = first = second = third = signature = ''
		greeting = f"Dear {self.everyone_role},"
		first = f"In the last 24 hours, the number of kills was {len(last_day)}."
		signature = "*THE EVIL GM*"

		if not final:
			title = f"## Day {day_count} and Report"
			if len(kill_logs) == 0:
				second = "In order to bring up the action I decided to give y'all a **free mission re-roll**."
				third = "Don't disappoint me again!"
			else:
				second = "### Kill list:\n"
				third = "Keep it going and you shall be rewarded graciously..."

				for kill_log in last_day:
					target = helper.get_member(self.guild, id=kill_log.mission.target_id)
					killer = helper.get_member(self.guild, id=kill_log.killer_id)
					second += f"**{target.name}** has been killed by **{killer.name}**.\n"

		else:
			title = f"## Day {day_count} and FINAL Report"
			second = "Time is up and the game must end!"
			if len(alive_players) == 1:
				third = f"**{self.alive_role.members[0].name}, being the sole survivor, is victorious!**\nYou have the honor to be my personal murder target! :smiling_imp: \n**MUAHAHAHAHAHAHA**\n"

			else:
				third = "It seems to me that we have multiple survivors...\n"
				third += "### Let's see how they compare:\n"

				max_kills: int = -1
				winners: list[Player] = []
				losers: list[Player] = []

				for survivor in alive_players:
					kill_count = helper.get_kill_count(survivor, kill_logs)
					max_kills = max(max_kills, kill_count)
					third += f"Number of {helper.get_member(self.guild, id=survivor.id).name}'s kills is {kill_count}.\n"

				for survivor in alive_players:
					if helper.get_kill_count(survivor, kill_logs) < max_kills:
						losers.append(survivor)
					else:
						winners.append(survivor)
				third += "\n"

				if len(losers) == 1:
					third += "Let's get rid of this coward with a low kill count:\n"
					third += f"***{helper.get_member(self.guild, id=losers[0].id).name}* has been brutally murdered by the *Evil GM***.\n"
				elif len(losers) > 1:
					third += "Let's get rid of these cowards with low kill counts:\n"
					for loser in losers:
						third += f"***{helper.get_member(self.guild, id=loser.id).name}* has been brutally murdered by the **Evil GM***.\n"
				third += "\n"

				if len(winners) == 1:
					third += f"**This leaves us with only one winner. And that is {helper.get_member(self.guild, id=winners[0].id).name}**.\n"
					third += f"You have the honor to be my personal murder target! :smiling_imp: \n**MUAHAHAHAHAHAHA**\n"
				elif len(winners) > 1:
					if len(losers) == 0:
						third += "With everyone being equally as good. I declare you all winners! But most importantly...\n"
					else:
						third += f"Now there are only {len(winners)} players left:\n"
						for winner in winners:
							third += f"{helper.get_member(self.guild, id=winner.id).name}\n"
						third += "I declare you all winners! But most importantly...\n"

					third += f"You have the honor to be my personal murder targets! :smiling_imp: \n**MUAHAHAHAHAHAHA**\n"

		await self.announcements_channel.send(f'{title}\n{greeting}\n{first}\n{second}\n{third}\n\n{signature}')

		if not final:
			self.data.day_number += 1
		return True

	async def mission_accomplished(self, killer: Player):
		self.data.load()
		players: list[Player] = self.data.players

		if killer.mission is None:
			raise AttributeError

		target: Player = helper.get_player(killer.mission.target_id, players)

		await self.send_private_message(killer, f"You successfully killed your target!")
		await self.kill_player(target, killer)

		if target.mission.target_id != killer.id:
			await self.assign_mission(killer, target.mission, True)
		elif len(players) <= 2:
			await self.assign_mission(killer, None, True)

	async def kill_player(self, target: Player, killer: Player | None = None):
		self.data.load()
		players = self.data.players
		day_count = self.data.day_number

		if killer is not None and killer.mission is None:
			raise AttributeError

		players.remove(target)
		target_member = helper.get_member_from_player(self.guild, target)
		await target_member.remove_roles(self.alive_role)
		await target_member.add_roles(self.dead_role)

		if killer is None:
			await self.send_private_message(target, f"You've been killed by {self.guild.me}! Spooky.")
		else:
			self.data.kill_logs.append(KillLog(killer.id, day_count, killer.mission))
			await self.send_private_message(target,
			                                f"You've been killed by {self.guild.me}! You'll get you're revenge one day.")

		for player in players:
			if player is not killer and player is not target:
				if player.mission and player.mission.target_id == target.id:
					mission = self.get_new_mission(player)
					await self.send_private_message(player, "Your target has been mysteriously killed.")
					await self.assign_mission(player, mission)

		self.data.save()

	def get_new_mission(self, player: Player) -> Mission:
		self.data.load()
		players = self.data.players
		locations = self.data.locations
		weapons = self.data.weapons

		restrictions: set[tuple[int, int]] = {(player.id, player.id)}
		untargeted: set[int] = set()
		targeted_once: set[int] = set()

		for p in players:
			t_count = 0
			for p2 in players:
				if p2.mission and p2.mission.target_id == p.id:
					t_count += 1
			if t_count == 0:
				untargeted.add(p.id)
			elif t_count == 1:
				targeted_once.add(p.id)

		if len(players) > 3:
			for other_player in players:
				if other_player is not player and other_player.mission.target_id == player.id:
					restrictions.add((player.id, other_player.id))

		target_id = tools.delegation_algorithm({player}, untargeted, targeted_once, restrictions)[0][1]
		location = random.choice(locations)
		weapon = random.choice(weapons)

		return Mission(target_id, location, weapon)

	async def assign_mission(self, player: Player, mission: Mission | None, get_reroll: bool = False):
		self.data.load()
		players = self.data.players

		channel = helper.get_channel_by_name(self.guild, str(player.id))

		if mission is None:
			await channel.send("**You have no more targets to kill!**")
			return

		target = helper.get_player(mission.target_id, players)
		target_member = helper.get_member_from_player(self.guild, target)

		player.mission = mission
		player.has_reroll = player.has_reroll or get_reroll

		self.data.save()

		embed = Embed(title="Assassination Mission",
		              description="This is a mission assigned uniquely to you. Kill the target at the specified location and with the specified weapon. Don't be seen.",
		              color=0xFF0000)
		embed.add_field(name="Target", value=f"Your target is the person named **{target_member.name}**.",
		                inline=False)

		embed.add_field(name="Location", value=f"You must murder your target at: **{mission.location}**.",
		                inline=True)
		embed.add_field(name="Weapon", value=f"Use **{mission.weapon}** to murder them!", inline=True)

		if player.has_reroll:
			footer_text = 'You have an available re-roll. Use it wisely!'
		else:
			footer_text = 'You currently have no available re-rolls.'

		embed.set_footer(text=footer_text)
		await channel.send(embed=embed)

	async def reroll_mission(self, player: Player, person: bool = False, location: bool = False, weapon: bool = False):
		self.data.load()
		players = self.data.players
		locations = self.data.locations
		weapons = self.data.weapons

		if not player.has_reroll:
			await self.send_private_message(player, "You don't have any re-rolls left!")
			return
		if not person and not location and not weapon:
			await self.send_private_message(player, "Please specify what you want to reroll (person, location, weapon, all).")
			return
		if person and len(players) <= 2:
			await self.send_private_message(player, "There aren't enough alive players to re-roll.")
			return

		mission = Mission(player.mission.target_id, player.mission.location, player.mission.weapon)

		if location:
			l_restrictions: set[tuple] = set()
			l_restrictions.add((0, player.mission.location))
			delegation = tools.delegation_algorithm({0}, set(locations), set(), l_restrictions)
			mission.location = list(delegation)[0][1]

		if weapon:
			w_restrictions: set[tuple] = set()
			w_restrictions.add((0, player.mission.weapon))
			delegation = tools.delegation_algorithm({0}, set(weapons), set(), w_restrictions)
			mission.weapon = list(delegation)[0][1]

		if person:
			not_targeted, targeted_once, targeted_twice = helper.categorize_by_n_of_targets(players)
			restrictions: set[tuple[int, int]] = {(player.id, player.id), (player.id, player.mission.target_id)}
			if len(players) >= 4:
				for p in players:
					if p.mission is not None and p.mission.target_id == player.id:
						restrictions.add((player.id, p.id))
			missions = tools.delegation_algorithm({player.id}, set(map(lambda pl: pl.id, not_targeted)),
			                                      set(map(lambda pl: pl.id, targeted_once)), restrictions)
			mission.target_id = list(missions)[0][1]

		player.has_reroll = False
		self.data.save()
		await self.assign_mission(player, player.mission)

	async def send_private_message(self, player: Player, message: str):
		channel = helper.get_player_channel(self.guild, player)
		await channel.send(message)

	async def fix_roles(self):
		self.data.load()
		players = self.data.players
		game_running = self.data.game_running
		for member in self.guild.members:
			if not game_running:
				if self.alive_role in member.roles or self.dead_role in member.roles:
					await member.remove_roles(self.alive_role, self.dead_role)
			else:
				player = helper.get_player(member.id, players)
				if player.is_alive:
					if self.dead_role in member.roles:
						await member.remove_roles(self.dead_role)
					if self.alive_role not in member.roles:
						await member.add_roles(self.alive_role)
				else:
					if self.dead_role not in member.roles:
						await member.add_roles(self.dead_role)
					if self.alive_role in member.roles:
						await member.remove_roles(self.alive_role)

	async def set_initial_missions(self):
		self.data.load()
		players = self.data.players
		locations = self.data.locations
		weapons = self.data.weapons

		player_order: list[Player] = tools.fisher_yates_shuffle(players)

		for i in range(len(players)):
			player = players[i]
			target = player_order[i]
			loc = random.choice(locations)
			wpn = random.choice(weapons)
			mission = Mission(target.id, loc, wpn)
			await self.assign_mission(player, mission, True)


servers: dict[int, DiscordServer] = {}


def get_server(guild_id: int):
	if guild_id in servers:
		return servers[guild_id]
	raise AttributeError


def add_server(guild_id: int, server: DiscordServer):
	if guild_id in servers:
		raise AttributeError
	servers[guild_id] = server


async def prepare_commands(bot: commands.Bot):
	for guild in bot.guilds:
		add_server(guild.id, DiscordServer(guild))