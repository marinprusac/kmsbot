import json
import random


def fisher_yates_shuffle(lst: list) -> list:
    lst2 = lst.copy()
    for i in range(len(lst2) - 1, 0, -1):
        j = random.randint(0, i - 1)
        lst2[i], lst2[j] = lst2[j], lst2[i]
    return lst2


class Mission:
    target: int
    location: str
    weapon: str

    def __init__(self, target: int, location: str, weapon: str):
        self.target = target
        self.location = location
        self.weapon = weapon


class Player:
    id: int
    alive: bool = True
    reroll: bool = True
    mission: Mission | None

    def __init__(self, id: int, mission: Mission | None = None):
        self.id = id
        self.mission = mission


def delegation_algorithm(pickers: set, options: set, secondary_options: set,
                         restrictions: set[tuple]) -> set[tuple]:
    not_targeting: set[int] = set(pickers)
    not_targeted: set[int] = set(options)
    targeted_once: set[int] = set(secondary_options)

    return_val: set[tuple[int, int]] = set()

    while len(not_targeting) > 0:
        min_index = -1
        min_count = -1
        break_out = False

        for i in not_targeting.copy():
            count = 0
            for j in not_targeted:
                if (i, j) not in restrictions:
                    count += 1
            if count == 0:
                for j in targeted_once:
                    if (i, j) not in restrictions:
                        targeted_once.remove(j)
                        not_targeting.remove(i)
                        return_val.add((i, j))
                        break_out = True
                        break
                break
            if min_count == -1 or count < min_count:
                min_count = count
                min_index = i

        if break_out:
            continue

        for j in not_targeted.copy():
            if (min_index, j) not in restrictions:
                return_val.add((min_index, j))
                not_targeted.remove(j)
                targeted_once.add(j)
                not_targeting.remove(min_index)
                break

    return return_val