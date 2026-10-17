extends Node
## Dev helper: times procedural construction.  -- --profile
var game: Game


func _ready() -> void:
	game = get_parent()
	_run.call_deferred()


func _t(label: String, f: Callable) -> void:
	var t0 := Time.get_ticks_usec()
	f.call()
	print("PROFILE %-28s %7.1f ms" % [label, (Time.get_ticks_usec() - t0) / 1000.0])


func _run() -> void:
	for i in 30:
		await get_tree().process_frame
	var tpl := {"floors": 3, "style": "windrise", "roof": "gable", "roof_col": Catalog.ROOF_COLORS[1], "wall_col": Catalog.WALL_COLORS[0],
		"pitch": 1.3, "chimney": -99.0, "ivy": 0.0, "id": 1, "seed": 5, "shape": "rect", "c": Vector2.ZERO, "size": Vector2(6.4, 4.4), "rot": 0.0, "base": 0.0}
	tpl.windows = BuildingView.default_windows(tpl)
	for style in ["windrise", "plaster", "stone"]:
		var d := tpl.duplicate(true)
		d.style = style
		var v := BuildingView.new()
		add_child(v)
		_t("house " + style, func(): v.build(d))
		_t("  its LODs", func(): MeshLod.apply_under(v))
		var pv := BuildingView.new()
		add_child(pv)
		_t("  draft (preview) build", func(): pv.build(d, [], true))
		pv.queue_free()
		v.queue_free()
	var r := tpl.duplicate(true)
	r.shape = "round"
	r.r = 2.2
	r.roof = "cone"
	r.windows = BuildingView.default_windows(r)
	var rv := BuildingView.new()
	add_child(rv)
	_t("tower windrise", func(): rv.build(r))
	var mb := MeshBuilder.new()
	var rng := RandomNumberGenerator.new()
	_t("roof slope 7x3", func(): Roofing.slope(mb, Vector3(0, 3, 0), Vector3(7, 3, 0), Vector3(0, 0, -3), Vector3(7, 0, -3), Color.RED, rng))
	_t("bevel_box x200", func():
		for i in 200:
			mb.bevel_box(Transform3D.IDENTITY, Vector3(0.6, 0.3, 0.5), 0.05, Color.WHITE))
	var surf := func(s: float) -> Dictionary:
		return {"p": Vector3(s, 0, 0), "n": Vector3.BACK, "g": 0.0, "low": -0.01, "top": 3.0}
	_t("masonry 10x3", func(): Masonry.lay(mb, surf, 0.0, 10.0, 0.0, 3.0, Color.WHITE, rng))
	_t("commit", func(): mb.commit())
	var wall := {"id": 3, "pts": PackedVector2Array([Vector2(-8, 0), Vector2(0, -1), Vector2(8, 0)]), "h": 3.4, "col": Catalog.STONE_COLORS[0], "style": "rendered"}
	var wv := WallView.new()
	add_child(wv)
	_t("wall rendered 16m", func(): wv.build(wall, game.glade.terrain, [{"s": 8.0, "w": 1.8}]))
	wall.style = "stone"
	_t("wall coursed 16m", func(): wv.build(wall, game.glade.terrain, [{"s": 8.0, "w": 1.8}]))
	_t("template town", func(): game.start_new("town"))
	get_tree().quit()
