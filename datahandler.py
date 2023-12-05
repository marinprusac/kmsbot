import json


class DataHandler:
    data: dict = {}

    @staticmethod
    def load():
        with open('./data.json') as file:
            DataHandler.data = json.loads(file.read())

    @staticmethod
    def save():
        with open('./data-backup.json', 'w') as backup, open('./data.json', 'r') as file:
            backup.write(file.read())
        try:
            with open('./data.json', 'w') as file:
                file.write(json.dumps(DataHandler.data, indent=4))
        except BaseException as err:
            with open('./data.json', 'w') as file, open('./data-backup.json', 'r') as backup:
                file.write(backup.read())
            raise err

    @staticmethod
    def get(field: str):
        if len(DataHandler.data) == 0:
            DataHandler.load()
        return DataHandler.data[field]

    @staticmethod
    def set(field: str, data):
        DataHandler.data[field] = data
        DataHandler.save()