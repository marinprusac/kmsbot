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
        with open(f'./{self.guild_id}.json') as file:
            data: AllData = jsonpickle.loads(file.read())
            self.__dict__.update(data.__dict__)

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