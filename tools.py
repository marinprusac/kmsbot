import random


def fisher_yates_shuffle(lst: list) -> list:
	lst2 = lst.copy()
	for i in range(len(lst2) - 1, 0, -1):
		j = random.randint(0, i - 1)
		lst2[i], lst2[j] = lst2[j], lst2[i]
	return lst2


def delegation_algorithm(pickers: set, options: set, secondary_options: set,
                         restrictions: set[tuple]) -> list[tuple]:

	return_val: list[tuple[int, int]] = []

	# loop while not everyone got their mission
	while len(pickers) > 0:

		break_out = False

		# look for those who have the least amount of options
		min_index = -1
		min_options = set()

		for i in pickers.copy():
			primary_candidates = set()
			for j in options:
				if (i, j) not in restrictions:
					primary_candidates.add(j)

			# if a picker has no primary options, then they have to choose a secondary option
			if len(primary_candidates) == 0:
				secondary_candidates = set()
				for j in secondary_options:
					if (i, j) not in restrictions:
						secondary_candidates.add(j)
				chosen = random.choice(list(secondary_candidates))
				secondary_options.remove(chosen)
				pickers.remove(i)
				return_val.append((i, chosen))
				break_out = True
				break

			# put the count as min count if the picker has the least number of options
			if min_index == -1 or len(primary_candidates) < len(min_options):
				min_options = primary_candidates
				min_index = i

		if break_out:
			continue

		# pick one of the options for the candidate with the least options
		chosen = random.choice(list(min_options))
		return_val.append((min_index, chosen))
		options.remove(chosen)
		secondary_options.add(chosen)
		pickers.remove(min_index)

	return return_val