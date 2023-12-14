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
		self.data = AllData(guild.id)
		self.data.setup_complete = self.setup()
		self.data.save()

	def setup(self) -> bool:
		try:
			self.everyone_role = self.guild.default_role
			self.registered_role = helper.get_role(self.guild, id=self.data.registered_role_id)
			self.dead_role = helper.get_role(self.guild, id=self.data.dead_role_id)
			self.alive_role = helper.get_role(self.guild, id=self.data.alive_role_id)
			self.admin_role = helper.get_role(self.guild, id=self.data.admin_role_id)
			self.announcements_channel = helper.get_channel(self.guild, self.data.announcements_channel_id)
			self.admin_channel = helper.get_channel(self.guild, self.data.admin_channel_id)
			self.private_category = helper.get_category(self.guild, self.data.private_category_id)
			return True
		except AttributeError:
			return False

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
		announce_text += f"Dear {self.everyone_role},\n"
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

		for player in self.data.players.copy():
			await self.remove_player(helper.get_member_from_player(self.guild, player), False)

		self.data.game_running = False
		self.data.players = []
		self.data.kill_logs = []
		self.data.day_number = 0
		self.data.save()
		await self.admin_channel.send("Game ended!")

	async def add_player(self, member: Member, special: bool = True):

		try:
			helper.get_player(member.id, self.data.players)
			await self.admin_channel.send("Player is already in game.")
			return
		except AttributeError:
			pass

		# add player to the list
		player = Player(member.id)
		self.data.players.append(player)
		self.data.save()

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
			await self.announcements_channel.send(f"{self.everyone_role}, "
			                                      f"**{member.display_name}** has been added to the game, watch out!")

	async def remove_player(self, member: Member, special: bool = True):
		try:
			player = helper.get_player(member.id, self.data.players)
		except AttributeError:
			await self.admin_channel.send("Player isn't in game.")
			return

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
			                                      f"**{member.display_name}** has been removed fom the game, phew.")

		self.data.save()

	async def day_report(self, final: bool = False):
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
					second += f"**{target.display_name}** has been killed by **{killer.display_name}**.\n"

		else:
			title = f"## Day {day_count} and FINAL Report"
			second = "Time is up and the game must end!"
			if len(alive_players) == 1:
				third = f"**{self.alive_role.members[0].display_name}, being the sole survivor, is victorious!**\nYou have the honor to be my personal murder target! :smiling_imp: \n**MUAHAHAHAHAHAHA**\n"

			else:
				third = "It seems to me that we have multiple survivors...\n"
				third += "### Let's see how they compare:\n"

				max_kills: int = -1
				winners: list[Player] = []
				losers: list[Player] = []

				for survivor in alive_players:
					kill_count = helper.get_kill_count(survivor, kill_logs)
					max_kills = max(max_kills, kill_count)
					third += f"Number of {helper.get_member(self.guild, id=survivor.id).display_name}'s kills is {kill_count}.\n"

				for survivor in alive_players:
					if helper.get_kill_count(survivor, kill_logs) < max_kills:
						losers.append(survivor)
					else:
						winners.append(survivor)
				third += "\n"

				if len(losers) == 1:
					third += "Let's get rid of this coward with a low kill count:\n"
					third += f"***{helper.get_member(self.guild, id=losers[0].id).display_name}* has been brutally murdered by the *Evil GM***.\n"
				elif len(losers) > 1:
					third += "Let's get rid of these cowards with low kill counts:\n"
					for loser in losers:
						third += f"***{helper.get_member(self.guild, id=loser.id).display_name}* has been brutally murdered by the **Evil GM***.\n"
				third += "\n"

				if len(winners) == 1:
					third += f"**This leaves us with only one winner. And that is {helper.get_member(self.guild, id=winners[0].id).display_name}**.\n"
					third += f"You have the honor to be my personal murder target! :smiling_imp: \n**MUAHAHAHAHAHAHA**\n"
				elif len(winners) > 1:
					if len(losers) == 0:
						third += "With everyone being equally as good. I declare you all winners! But most importantly...\n"
					else:
						third += f"Now there are only {len(winners)} players left:\n"
						for winner in winners:
							third += f"{helper.get_member(self.guild, id=winner.id).display_name}\n"
						third += "I declare you all winners! But most importantly...\n"

					third += f"You have the honor to be my personal murder targets! :smiling_imp: \n**MUAHAHAHAHAHAHA**\n"

		await self.announcements_channel.send(f'{title}\n{greeting}\n{first}\n{second}\n{third}\n\n{signature}')

		if not final:
			self.data.day_number += 1
		return True

	async def mission_accomplished(self, killer: Player):
		players = self.data.players

		if killer.mission is None:
			await self.send_private_message(killer, "But... you don't have any missions.")
			return

		target: Player = helper.get_player(killer.mission.target_id, players)

		if not target.is_alive:
			await self.send_private_message(killer,
			                                "Something is wrong. Your target is already dead. Here's a new one.")
			mission = self.get_new_mission(killer)
			await self.assign_mission(killer, mission, True)
			return

		await self.send_private_message(killer, f"You successfully killed your target!")
		await self.kill_player(target, killer)

		alive_players = helper.get_alive_players(players)

		if len(alive_players) < 2:
			await self.assign_mission(killer, None, True)
		elif target.mission.target_id != killer.id:
			await self.assign_mission(killer, target.mission, True)
		else:
			mission = self.get_new_mission(killer)
			await self.assign_mission(killer, mission, True)

	async def kill_player(self, target: Player, killer: Player | None = None):
		alive_players = helper.get_alive_players(self.data.players)
		day_count = self.data.day_number

		if not target.is_alive:
			await self.admin_channel.send("Player is already dead.")
			return

		target.is_alive = False
		target_member = helper.get_member_from_player(self.guild, target)

		await target_member.remove_roles(self.alive_role)
		await target_member.add_roles(self.dead_role)

		if killer is None:
			await self.send_private_message(target, f"You've been killed by {self.guild.me.display_name}! Spooky.")
		else:
			killer_member = helper.get_member_from_player(self.guild, killer)
			self.data.kill_logs.append(KillLog(killer.id, day_count, killer.mission))
			await self.send_private_message(target,
			                                f"You've been killed by {killer_member.display_name}! You'll get your revenge one day.")

		for player in alive_players:
			if player.is_alive and player is not killer and player is not target:
				if player.mission and player.mission.target_id == target.id:
					mission = self.get_new_mission(player)
					await self.send_private_message(player, "Your target has been mysteriously killed.")
					await self.assign_mission(player, mission)

		self.data.save()
		await self.admin_channel.send("Player has been killed.")

	async def revive_player(self, player: Player):
		member = helper.get_member_from_player(self.guild, player)

		if player.is_alive:
			await self.admin_channel.send(f"Player is already alive!")
			return

		player.is_alive = True
		await member.add_roles(self.alive_role)
		await member.remove_roles(self.dead_role)

		# Remove kill log
		for log in self.data.kill_logs.copy():
			if log.mission.target_id == player.id:
				self.data.kill_logs.remove(log)
				break

		# Announcements and mission delegation
		mission = self.get_new_mission(player)
		await self.send_private_message(player, "You've been revived!")
		await self.announcements_channel.send(f"{member.mention} has been revived, watch out!")
		await self.assign_mission(player, mission, False)
		await self.admin_channel.send(f"{member.mention} has been revived.")
		self.data.save()

	def get_new_mission(self, player: Player) -> Mission | None:
		alive_players = helper.get_alive_players(self.data.players)
		locations = self.data.locations
		weapons = self.data.weapons

		if len(alive_players) < 2:
			return None

		restrictions: set[tuple[int, int]] = {(player.id, player.id)}

		untargeted, targeted_once, targeted_twice, not_targeting = helper.categorize_by_n_of_targets(alive_players)

		if len(alive_players) > 3:
			for other_player in alive_players:
				if other_player is not player and other_player.mission.target_id == player.id:
					restrictions.add((player.id, other_player.id))

		target_id = tools.delegation_algorithm({player.id}, set(player.id for player in untargeted),
		                                       set(player.id for player in targeted_once), restrictions)[0][1]
		location = random.choice(locations)
		weapon = random.choice(weapons)

		return Mission(target_id, location, weapon)

	async def assign_mission(self, player: Player, mission: Mission | None, get_reroll: bool = False):
		channel = helper.get_player_channel(self.guild, player)

		if mission is None:
			await channel.send("**You have no more targets to kill!**")
			player.mission = None
			return

		target = helper.get_player(mission.target_id, self.data.players)
		target_member = helper.get_member_from_player(self.guild, target)

		player.mission = mission
		player.has_reroll = player.has_reroll or get_reroll

		self.data.save()

		embed = Embed(title="Assassination Mission",
		              description="This is a mission assigned uniquely to you. Kill the target at the specified location and with the specified weapon. Don't be seen.",
		              color=0xFF0000)
		embed.add_field(name="Target", value=f"Your target is the person named **{target_member.display_name}**.",
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
		alive_players = helper.get_alive_players(self.data.players)
		locations = self.data.locations
		weapons = self.data.weapons

		if player.mission is None:
			await self.send_private_message(player, "You don't have a mission.")
			return
		if not player.has_reroll:
			await self.send_private_message(player, "You don't have any re-rolls left!")
			return
		if not person and not location and not weapon:
			await self.send_private_message(player,
			                                "Please specify what you want to reroll (person, location, weapon, all).")
			return
		if person and len(alive_players) <= 2:
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
			not_targeted, targeted_once, targeted_twice, not_targeting = helper.categorize_by_n_of_targets(
				alive_players)
			restrictions: set[tuple[int, int]] = {(player.id, player.id), (player.id, player.mission.target_id)}
			if len(alive_players) >= 4:
				for p in alive_players:
					if p.mission is not None and p.mission.target_id == player.id:
						restrictions.add((player.id, p.id))
			missions = tools.delegation_algorithm({player.id}, set(map(lambda pl: pl.id, not_targeted)),
			                                      set(map(lambda pl: pl.id, targeted_once)), restrictions)
			mission.target_id = list(missions)[0][1]

		player.has_reroll = False
		self.data.save()
		await self.assign_mission(player, mission)

	async def send_private_message(self, player: Player, message: str):
		channel = helper.get_player_channel(self.guild, player)
		await channel.send(message)

	async def fix_roles(self):
		game_running = self.data.game_running
		for member in self.guild.members:
			if not game_running:
				if self.alive_role in member.roles or self.dead_role in member.roles:
					await member.remove_roles(self.alive_role, self.dead_role)
			else:
				player = helper.get_player(member.id, self.data.players)
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
		alive_players = helper.get_alive_players(self.data.players)
		locations = self.data.locations
		weapons = self.data.weapons

		player_order: list[Player] = tools.fisher_yates_shuffle(alive_players)

		for i in range(len(alive_players)):
			player = alive_players[i]
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


def remove_server(guild_id: int):
	if guild_id not in servers:
		raise AttributeError
	servers.pop(guild_id)


async def load_guilds(bot: commands.Bot):
	for guild in bot.guilds:
		add_server(guild.id, DiscordServer(guild))