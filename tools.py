import random


def fisher_yates_shuffle(lst: list) -> list:
    lst2 = lst.copy()
    for i in range(len(lst2) - 1, 0, -1):
        j = random.randint(0, i - 1)
        lst2[i], lst2[j] = lst2[j], lst2[i]
    return lst2


def delegation_algorithm(pickers: set, options: set, secondary_options: set,
                         restrictions: set[tuple]) -> list[tuple]:
    not_targeting: set[int] = set(pickers)
    not_targeted: set[int] = set(options)
    targeted_once: set[int] = set(secondary_options)

    return_val: list[tuple[int, int]] = []

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
                        return_val.append((i, j))
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
                return_val.append((min_index, j))
                not_targeted.remove(j)
                targeted_once.add(j)
                not_targeting.remove(min_index)
                break

    return return_val