import jsonpickle


class Mission:
	target_id: int
	location: str
	weapon: str

	def __init__(self, target: int, location: str, weapon: str):
		self.target_id = target
		self.location = location
		self.weapon = weapon


class Player:
	id: int
	is_alive: bool
	has_reroll: bool
	mission: Mission | None

	def __eq__(self, other):
		return self.id == other.id

	def __init__(self, id: int, is_alive: bool = True, has_reroll: bool = True, mission: Mission | None = None):
		self.id = id
		self.mission = mission
		self.is_alive = is_alive
		self.has_reroll = has_reroll


class KillLog:
	killer_id: int
	day_number: int
	mission: Mission

	def __init__(self, killer_id: int, day_number: int, mission: Mission):
		self.killer_id = killer_id
		self.day_number = day_number
		self.mission = mission


class AllData:
	guild_id: int

	setup_complete: bool

	admin_channel_id: int
	announcements_channel_id: int
	private_category_id: int

	registered_role_id: int
	alive_role_id: int
	dead_role_id: int
	admin_role_id: int

	game_running: bool
	day_number: int
	players: list[Player]
	kill_logs: list[KillLog]
	locations: list[str]
	weapons: list[str]

	def __init__(self, guild_id: int):
		self.guild_id = guild_id
		self.load()
		self.guild_id = guild_id

	def load(self):
		try:
			with open(f'./{self.guild_id}.json') as file:
				data: AllData = jsonpickle.loads(file.read())
				self.__dict__.update(data.__dict__)

		except BaseException:
			self.setup_complete = False

			self.admin_channel_id = 0
			self.announcements_channel_id = 0
			self.private_category_id = 0

			self.registered_role_id = 0
			self.alive_role_id = 0
			self.dead_role_id = 0
			self.admin_role_id = 0

			self.game_running = False
			self.day_number = 0
			self.players = []
			self.kill_logs = []
			self.locations = []
			self.weapons = []

			with open(f'./{self.guild_id}-backup.json', 'w') as backup, open(f'./{self.guild_id}.json', 'w') as file:
				backup.write(jsonpickle.dumps(self, indent=4))
				file.write(jsonpickle.dumps(self, indent=4))

	def save(self):
		with open(f'./{self.guild_id}-backup.json', 'w') as backup, open(f'./{self.guild_id}.json', 'r') as file:
			backup.write(file.read())
		try:
			with open(f'./{self.guild_id}.json', 'w') as file:
				file.write(jsonpickle.dumps(self, indent=4))
		except BaseException as err:
			with open(f'./{self.guild_id}.json', 'w') as file, open(f'./{self.guild_id}-backup.json', 'r') as backup:
				file.write(backup.read())
			raise err