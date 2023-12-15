import random
import tools
from datahandler import AllData, Player, Mission, KillLog
import helper
from guildmanager import GuildManager
from enum import Enum

class GameManager:

	guild_manager: GuildManager
	data: AllData

	def __init__(self, guild_manager: GuildManager):
		self.guild_manager = guild_manager
		self.data = AllData(guild_manager.guild.id)
		self.data.setup_complete = self.guild_manager.setup(self.data.registered_role_id, self.data.alive_role_id,
		                                                    self.data.dead_role_id, self.data.admin_role_id,
		                                                    self.data.announcements_channel_id, self.data.admin_channel_id,
		                                                    self.data.private_category_id)
		self.data.save()

	class StartGameResult(Enum):
		SUCCESS = 0
		NOT_ENOUGH_PLAYERS = 1
		NOT_ENOUGH_LOCATIONS = 2
		NOT_ENOUGH_WEAPONS = 3
		UNKNOWN_PLAYER = 4

	def start_game(self, registered_players: list[Player]) -> StartGameResult:

		# check if the conditions are met
		if len(registered_players) < 2:
			return self.StartGameResult.NOT_ENOUGH_PLAYERS
		if len(self.data.locations) < 1:
			return self.StartGameResult.NOT_ENOUGH_LOCATIONS
		if len(self.data.weapons) < 1:
			return self.StartGameResult.NOT_ENOUGH_WEAPONS
		if any(p not in self.data.players for p in registered_players):
			return self.StartGameResult.UNKNOWN_PLAYER

		# assign initial missions
		player_order: list[Player] = tools.fisher_yates_shuffle(registered_players)

		for i in range(len(registered_players)):
			player = registered_players[i]
			player.in_game = True
			player.is_alive = True

			target = player_order[i]
			loc = random.choice(self.data.locations)
			wpn = random.choice(self.data.weapons)

			mission = Mission(target.id, loc, wpn)
			player.mission = mission
			player.has_reroll = True

		# finalize data and return
		self.data.game_running = True
		self.data.day_number = 1
		self.data.save()

		return self.StartGameResult.SUCCESS

	def end_game(self):

		for player in self.data.players:
			player.in_game = False

		self.data.game_running = False
		self.data.players = []
		self.data.kill_logs = []
		self.data.day_number = 0
		self.data.save()

	def player_joined(self, player: Player):
		self.data.players.append(player)
		self.data.save()

	def player_left(self, player: Player):
		self.data.players.remove(player)
		for other_player in self.data.players:
			if other_player.mission and other_player.mission.target_id == player.id:
				mission = self.get_new_mission(other_player)
				other_player.mission = mission
		self.data.save()

	def end_day(self, final: bool = False):
		day_count: int = self.data.day_number
		kill_logs: list[KillLog] = self.data.kill_logs
		last_day: list[KillLog] = list(filter(lambda log: log.day_number == day_count, kill_logs))
		players: list[Player] = self.data.players
		alive_players: list[Player] = list(filter(lambda player: player.is_alive and player.in_game, players))
		final = final or len(alive_players) == 1

		# if there were no kills last night, grant rerolls
		if len(last_day) == 0:
			for p in players:
				if not p.has_reroll:
					p.has_reroll = True

		if not final:
			self.data.day_number += 1

		self.data.save()

	def mission_accomplished(self, killer: Player) -> bool:
		players = self.data.players

		if killer.mission is None:
			return False

		target: Player = helper.get_player(killer.mission.target_id, players)

		self.kill_player(target, killer)

		alive_players = helper.get_alive_players(players)

		if len(alive_players) < 2:
			killer.mission = None
			killer.has_reroll = True
		elif target.mission.target_id != killer.id:
			killer.mission = target.mission
		else:
			mission = self.get_new_mission(killer)
			killer.mission = mission

		killer.has_reroll = True
		self.data.save()
		return True

	def kill_player(self, target: Player, killer: Player | None = None):
		alive_players = helper.get_alive_players(self.data.players)
		day_count = self.data.day_number

		target.is_alive = False

		if killer is None:
			pass
		else:
			self.data.kill_logs.append(KillLog(killer.id, day_count, killer.mission))

		for player in alive_players:
			if player.is_alive and player is not killer and player is not target:
				if player.mission and player.mission.target_id == target.id:
					mission = self.get_new_mission(player)
					player.mission = mission
		self.data.save()

	async def revive_player(self, player: Player):

		player.is_alive = True

		# Remove kill log
		for log in self.data.kill_logs.copy():
			if log.mission.target_id == player.id:
				self.data.kill_logs.remove(log)
				break

		# Announcements and mission delegation
		mission = self.get_new_mission(player)
		player.mission = mission
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

	class RerollResult(Enum):
		SUCCESS = 0
		NO_MISSION = 1
		NO_REROLLS = 2
		NOT_ENOUGH_PLAYERS = 3
		NOT_SPECIFIED = 4

	def reroll_mission(self, player: Player, person: bool = False, location: bool = False, weapon: bool = False)\
			-> RerollResult:
		alive_players = helper.get_alive_players(self.data.players)
		locations = self.data.locations
		weapons = self.data.weapons

		if player.mission is None:
			return self.RerollResult.NO_MISSION
		if not player.has_reroll:
			return self.RerollResult.NO_REROLLS
		if not person and not location and not weapon:
			return self.RerollResult.NOT_SPECIFIED
		if person and len(alive_players) <= 2:
			return self.RerollResult.NOT_ENOUGH_PLAYERS

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
		player.mission = mission
		self.data.save()
		return self.RerollResult.SUCCESS


servers: dict[int, GameManager] = {}


def get_server(guild_id: int):
	if guild_id in servers:
		return servers[guild_id]
	raise AttributeError


def add_server(guild_id: int, server: GameManager):
	if guild_id in servers:
		raise AttributeError
	servers[guild_id] = server


def remove_server(guild_id: int):
	if guild_id not in servers:
		raise AttributeError
	servers.pop(guild_id)