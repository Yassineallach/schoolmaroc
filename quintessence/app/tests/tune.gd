extends SceneTree
## Tuning probe: greedy bot plays all 4 Readings per Night (targets ignored) and reports totals.

func _init() -> void:
	var totals := [[], [], []]
	for seed in 120:
		var s := RunState.new()
		s.new_run(5000 + seed)
		s.choose_patron(0)
		for night in 3:
			s.night = night
			s.phase = "intro"
			s.start_night()
			var sum := 0
			for r in 4:
				var pick := _best(s)
				for q in pick[0].size():
					s.place(int(pick[0][q]["id"]), pick[1][q])
				# bypass target: compute and read
				var res := s.preview()
				sum += int(res["insight"])
				s.insight = -1000000
				s.read()
				if s.phase != "play":
					break
			totals[night].append(sum)
	for n in 3:
		var a: Array = totals[n]
		a.sort()
		print("night %d: p10 %d  p25 %d  median %d  p75 %d" % [n, a[int(a.size()*0.1)], a[int(a.size()*0.25)], a[a.size()/2], a[int(a.size()*0.75)]])
	quit()

func _best(s: RunState) -> Array:
	var best := []
	var best_v := -1
	var n := s.hand.size()
	var blocked := s.blocked_positions()
	var open: Array = []
	for p in 3:
		if not blocked.has(p):
			open.append(p)
	for i in n:
		for j in range(i, n):
			for k in range(j, n):
				var idx := {i: true, j: true, k: true}
				var cards: Array = []
				for key in idx.keys():
					cards.append(s.hand[key])
				for a in open:
					for b in open:
						for c in open:
							var perm := [a, b, c].slice(0, cards.size())
							var uniq := {}
							for x in perm: uniq[x] = true
							if uniq.size() != perm.size(): continue
							var sp: Array = [null, null, null]
							for q in cards.size():
								sp[perm[q]] = cards[q]
							var v := int(Scoring.evaluate(sp, s.score_context())["insight"])
							if v > best_v:
								best_v = v
								best = [cards, perm]
	return best
