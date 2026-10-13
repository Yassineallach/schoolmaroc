class_name Life
extends Node3D
## Spawns and balances the glade's wildlife based on what has been built:
## sheep in the meadow, ducks on ponds, chickens near cottages, birds that
## perch on walls and roofs, and butterflies on warm days.

var glade: Glade
var day: DayCycle
var sheep: Array = []
var ducks: Array = []
var chickens: Array = []
var birds: Array = []
var butterflies: Array = []
var cats: Array = []
var kois: Array = []
var slimes: Array = []
var crystalflies: Array = []
var wildlife: Array = []
var _rng := RandomNumberGenerator.new()
var _rebalance_in := 0.5
var enabled := true


func setup(g: Glade, d: DayCycle) -> void:
	glade = g
	day = d
	_rng.seed = 4242
	glade.changed.connect(func(): _rebalance_in = 1.5)
	day.changed.connect(func(): _rebalance_in = minf(_rebalance_in, 1.0) if _rebalance_in > 0 else 1.0)


func clear() -> void:
	for list in [sheep, ducks, chickens, birds, butterflies, cats, kois, slimes, crystalflies, wildlife]:
		for c in list:
			c.queue_free()
		list.clear()
	_rebalance_in = 0.5


func _process(delta: float) -> void:
	if not enabled:
		return
	_update_grass_pushers()
	if _rebalance_in > 0.0:
		_rebalance_in -= delta
		if _rebalance_in <= 0.0:
			_rebalance()


func _rebalance() -> void:
	# --- sheep: a small flock always roams the meadow
	_balance(sheep, 5, func(): return _spawn_land("sheep", Sheep))
	for s in sheep:
		s.flock = sheep
	# --- wildlife: a pair of deer and a fox near the meadow's edge, and a
	# donkey and an alpaca that keep to the cottages once there are homes
	var homes0: Array = glade.list_of("buildings")
	var kinds: Array = ["q_deer", "q_deer", "q_fox"]
	if not homes0.is_empty():
		kinds.append_array(["q_donkey", "q_alpaca"])
	while wildlife.size() > kinds.size():
		wildlife.pop_back().queue_free()
	while wildlife.size() < kinds.size():
		var kind: String = kinds[wildlife.size()]
		if not ModelLib.has_model(kind):
			break
		var centre := Vector2.ZERO
		if kind == "q_donkey" or kind == "q_alpaca":
			var hb: Dictionary = homes0[_rng.randi() % homes0.size()]
			centre = hb.c + Vector2(_rng.randf_range(-5, 5), _rng.randf_range(-5, 5))
		else:
			var a0 := _rng.randf() * TAU
			centre = Vector2(cos(a0), sin(a0)) * _rng.randf_range(11.0, 16.0)
		var w := _spawn_land(kind, Wildlife, centre) as Wildlife
		if w == null:
			break
		w.roam_center = centre
		w.roam_radius = 5.0 if kind == "q_fox" else 6.0
		wildlife.append(w)
	# --- ducks: families on big enough ponds
	var cells := glade.water_cells()
	var families := clampi(cells / 40, 0, 3)
	var parents: Array = ducks.filter(func(d): return d.leader == null)
	while parents.size() > families:
		var p = parents.pop_back()
		for d in ducks.duplicate():
			if d.leader == p:
				ducks.erase(d)
				d.queue_free()
		ducks.erase(p)
		p.queue_free()
	while parents.size() < families:
		var spot = glade.random_water_point(_rng)
		if spot == null:
			break
		var parent := _spawn("duck", Duck, spot) as Duck
		ducks.append(parent)
		parents.append(parent)
		var prev: Node3D = parent
		for i in _rng.randi_range(1, 3):
			var kid := _spawn("duckling", Duck, spot + Vector2(0.4 * (i + 1), 0)) as Duck
			kid.scale = Vector3.ONE * 0.7
			kid.leader = prev
			ducks.append(kid)
			prev = kid
	# remove ducks stranded by terrain edits
	for d in ducks.duplicate():
		if not glade.terrain.is_water(d.global_position.x, d.global_position.z):
			if d.leader == null:
				var p2 = glade.random_water_point(_rng)
				if p2 != null:
					d.global_position = Vector3(p2.x, Terrain.WATER_LEVEL, p2.y)
				else:
					ducks.erase(d)
					d.queue_free()
	# --- chickens around cottages
	var homes: Array = glade.list_of("buildings")
	var want_chickens := mini(homes.size() * 2, 6)
	_balance(chickens, want_chickens, func():
		var b: Dictionary = homes[_rng.randi() % homes.size()]
		var c = _spawn_land("chicken", Chicken, b.c + Vector2(_rng.randf_range(-4, 4), _rng.randf_range(-4, 4)))
		if c:
			c.home = b.c
		return c)
	# --- cats wandering between cottages
	_balance(cats, mini(homes.size(), 3), func():
		var b3: Dictionary = homes[_rng.randi() % homes.size()]
		var c3 = _spawn_land("cat" if _rng.randf() < 0.6 else "cat_black", Cat, b3.c + Vector2(_rng.randf_range(-4, 4), _rng.randf_range(-4, 4)))
		if c3:
			c3.home = b3.c
		return c3)
	# --- koi in ponds
	_balance(kois, clampi(cells / 18, 0, 8), func():
		var spot2 = glade.random_water_point(_rng)
		if spot2 == null:
			return null
		return _spawn("koi" if _rng.randf() < 0.6 else "koi_white", Koi, spot2))
	for k in kois.duplicate():
		if not glade.terrain.is_water(k.global_position.x, k.global_position.z):
			kois.erase(k)
			k.queue_free()
	# --- slimes bouncing about the meadow edges
	_balance(slimes, 4, func():
		var a := _rng.randf() * TAU
		var spot := Vector2(cos(a), sin(a)) * _rng.randf_range(10.0, 18.0)
		return _spawn_land("slime" if _rng.randf() < 0.55 else "slime_blue", Slime, spot))
	# --- glowing crystalflies drifting about at dusk and night
	_balance(crystalflies, 7 if day.night > 0.35 else 0, func():
		var home2 := Vector3(_rng.randf_range(-14, 14), 0, _rng.randf_range(-14, 14))
		var cf := _spawn("crystalfly", Butterfly, Vector2(home2.x, home2.z)) as Butterfly
		cf.home = home2
		return cf)
	# --- birds
	var perches := glade.perches()
	_balance(birds, 3 if perches.size() < 4 else 6, func():
		var b2 := _spawn("bird", Bird, Vector2(_rng.randf_range(-10, 10), _rng.randf_range(-10, 10))) as Bird
		b2.global_position.y = 10.0
		return b2)
	# --- butterflies on warm days
	var warm: bool = day.season <= 1 and day.night < 0.4
	var flowers: Array = glade.list_of("props").filter(func(p): return String(p.kind).begins_with("flowers"))
	_balance(butterflies, 5 if warm else 0, func():
		var home := Vector3(_rng.randf_range(-12, 12), 0, _rng.randf_range(-12, 12))
		if not flowers.is_empty():
			home = flowers[_rng.randi() % flowers.size()].p
		var bf := _spawn("butterfly", Butterfly, Vector2(home.x, home.z)) as Butterfly
		bf.home = home
		return bf)


func _balance(list: Array, want: int, spawn: Callable) -> void:
	while list.size() > want:
		var c = list.pop_back()
		c.queue_free()
	var guard := 0
	while list.size() < want and guard < want * 3:
		guard += 1
		var c = spawn.call()
		if c:
			list.append(c)


func _spawn(kind: String, script_class, pos: Vector2) -> Creature:
	var c: Creature = script_class.new()
	c.setup(glade, kind, _rng.randi())
	add_child(c)
	c.global_position = Vector3(pos.x, c.ground_y(pos), pos.y)
	return c


func _spawn_land(kind: String, script_class, near := Vector2.INF) -> Creature:
	for i in 20:
		var p := near if near != Vector2.INF and i < 10 else Vector2(_rng.randf_range(-16, 16), _rng.randf_range(-16, 16))
		if near != Vector2.INF and i < 10:
			p += Vector2(_rng.randf_range(-2, 2), _rng.randf_range(-2, 2))
		if not glade.is_blocked(p):
			return _spawn(kind, script_class, p)
	return null


## Ray-sphere test against all creatures; returns the nearest hit or null.
func pick(origin: Vector3, dir: Vector3) -> Creature:
	var best: Creature = null
	var best_t := INF
	for list in [sheep, ducks, chickens, birds, butterflies, cats, kois, slimes, crystalflies, wildlife]:
		for c in list:
			var center: Vector3 = c.global_position + Vector3.UP * 0.4 * c.scale.x
			var r: float = c.pet_radius * c.scale.x + 0.25
			var oc := center - origin
			var t := oc.dot(dir)
			if t < 0.0:
				continue
			var d2 := oc.length_squared() - t * t
			if d2 < r * r and t < best_t:
				best_t = t
				best = c
	return best


## Sheep, chickens, cats and slimes part the meadow grass as they walk.
func _update_grass_pushers() -> void:
	if glade == null or glade.grass == null:
		return
	var list: Array = []
	for group in [[sheep, 0.75], [slimes, 0.6], [cats, 0.45], [chickens, 0.4], [wildlife, 0.7]]:
		for c in group[0]:
			if is_instance_valid(c) and c.is_inside_tree():
				var p: Vector3 = c.global_position
				list.append(Vector4(p.x, p.y, p.z, group[1]))
	glade.grass.set_pushers(list)
