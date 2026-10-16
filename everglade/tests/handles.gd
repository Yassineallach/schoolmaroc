extends Node
## Dev helper: drives the Explore tool's edit handles like a finger would and
## checks each edit lands.  -- --handles=/tmp/dir
var game: Game
var out := ""
var fails := 0


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--handles="):
			out = a.trim_prefix("--handles=")
	DirAccess.make_dir_recursive_absolute(out)
	game = get_parent()
	_run.call_deferred()


func _check(name: String, ok: bool) -> void:
	print(("PASS " if ok else "FAIL ") + name)
	if not ok:
		fails += 1


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _shot(n: String) -> void:
	await _frames(20)
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(n + ".png"))


## Grabs the first handle of `kind` and drags it by `delta` pixels (or to a
## ground point when `to` is given).
func _pull(kind: String, delta: Vector2, to = null) -> bool:
	var hand: HandTool = game.tool
	hand._sync_handles()
	for h in hand._handles:
		if h.kind != kind:
			continue
		var cam := game.rig.camera
		var a := cam.unproject_position(h.pos)
		var b := a + delta if to == null else cam.unproject_position(to)
		if not hand.press(a):
			return false
		for k in 8:
			hand.drag(a.lerp(b, (k + 1) / 8.0))
			await _frames(1)
		hand.release(b)
		await _frames(4)
		return true
	return false


func _focus(p: Vector3, dist: float) -> void:
	game.rig.focus_on(p, dist)
	game.rig.snap()
	await _frames(10)


func _run() -> void:
	await _frames(60)
	game.start_new("hamlet")
	game.life.enabled = false
	game.life.clear()
	game.set_tool("hand")
	var g := game.glade
	# --- wall: height and reshape
	var wall: Dictionary = g.data.walls[0]
	var mid := Geo.point_at(wall.pts, Geo.length(wall.pts) * 0.5)
	await _focus(Geo.v3(mid, 1.5), 14.0)
	game.select(wall.id)
	await _frames(5)
	await _shot("1_wall_handles")
	var h0: float = wall.get("h", 2.4)
	await _pull("wall_h", Vector2(0, -90))
	wall = g.find(wall.id).item
	_check("wall height handle raises the wall (%.1f -> %.1f)" % [h0, wall.h], wall.h > h0 + 0.3)
	var p0: Vector2 = wall.pts[0]
	await _pull("pt", Vector2(70, 40))
	wall = g.find(wall.id).item
	_check("wall point handle reshapes the wall", (wall.pts[0] as Vector2).distance_to(p0) > 0.3)
	# --- house: floors, pitch, stretch, turn
	var house: Dictionary = {}
	for b in g.data.buildings:
		if b.shape == "rect" and b.roof != "flat":
			house = b
			break
	await _focus(Geo.v3(house.c, house.base + 3.0), 18.0)
	game.select(house.id)
	await _frames(5)
	await _shot("2_house_handles")
	var f0: int = house.floors
	await _pull("floors", Vector2(0, -70))
	house = g.find(house.id).item
	_check("floors handle adds a storey (%d -> %d)" % [f0, house.floors], house.floors == mini(f0 + 1, 6))
	var pitch0: float = house.pitch
	await _pull("pitch", Vector2(0, -60))
	house = g.find(house.id).item
	_check("roof handle steepens the roof (%.2f -> %.2f)" % [pitch0, house.pitch], house.pitch > pitch0 + 0.1)
	var sx0: float = house.size.x
	var rot: float = house.get("rot", 0.0)
	var target := Geo.v3(house.c + Vector2(cos(rot), sin(rot)) * (sx0 * 0.5 + 1.5), house.base)
	await _pull("size_x", Vector2.ZERO, target)
	house = g.find(house.id).item
	_check("side handle stretches the house (%.1f -> %.1f)" % [sx0, house.size.x], house.size.x > sx0 + 0.6)
	var r0: float = house.get("rot", 0.0)
	await _pull("rotate", Vector2(-80, 60))
	house = g.find(house.id).item
	_check("rotate handle turns the house", absf(house.get("rot", 0.0) - r0) > 0.05)
	# --- copy
	var n0: int = g.data.buildings.size()
	game._on_inspector_action("clone", true)
	await _frames(5)
	_check("copy duplicates the house", g.data.buildings.size() == n0 + 1)
	_check("the copy gets selected", game.selected_id != house.id and game.selected_id >= 0)
	await _shot("3_after_edits")
	# --- undo walks the edits back
	var undo0: int = g.undo_stack.size()
	game.do_undo()
	await _frames(3)
	_check("undo removes the copy", g.data.buildings.size() == n0 and g.undo_stack.size() == undo0 - 1)
	# --- roof curve: drag the roof handle sideways
	house = g.find(house.id).item
	game.select(house.id)
	await _frames(5)
	await _pull("pitch", Vector2(110, 0))
	house = g.find(house.id).item
	_check("sideways roof drag rounds the roof (curve %.2f)" % house.get("curve", 0.0), absf(house.get("curve", 0.0)) > 0.3)
	await _focus(Geo.v3(house.c, house.base + 3.0), 16.0)
	await _shot("4_curved_roof")
	# --- wall points, straighten, cut
	wall = g.data.walls[0]
	game.select(wall.id)
	game._on_inspector_action("more_pts", true)
	wall = g.find(wall.id).item
	_check("more points adds reshape dots", int(wall.get("knots", 9)) == 12)
	game._on_inspector_action("straighten", true)
	wall = g.find(wall.id).item
	var pts: PackedVector2Array = wall.pts
	var chord := pts[0].distance_to(pts[pts.size() - 1])
	_check("straighten makes the wall straight", absf(Geo.length(pts) - chord) < 0.05)
	var n_walls: int = g.data.walls.size()
	game._on_inspector_action("cut", true)
	var cut_at := pts[0].lerp(pts[pts.size() - 1], 0.5)
	(game.tool as HandTool).tap(game.rig.camera.unproject_position(Geo.v3(cut_at, g.terrain.height_at_v(cut_at))))
	await _frames(3)
	_check("cut splits the wall in two", g.data.walls.size() == n_walls + 1)
	# --- joined houses: a small house pushed into a big one squares up to it
	game.select(-1)
	var big: Dictionary = house
	var rot0: float = big.get("rot", 0.0)
	var ax := Vector2(cos(rot0), sin(rot0))
	var az := Vector2(-sin(rot0), cos(rot0))
	var small := g.add_building({"shape": "rect", "c": (big.c as Vector2) + az * (big.size.y * 0.5 + 1.6), "size": Vector2(4.0, 3.6),
			"rot": rot0 + PI * 0.5 + 0.12, "floors": 1, "style": big.style, "roof": "gable", "pitch": 1.1,
			"roof_col": big.roof_col, "wall_col": big.wall_col, "chimney": BuildingView.NO_CHIMNEY})
	await _frames(3)
	var drot := wrapf(float(small.rot) - rot0, -PI, PI)
	_check("joined house squares up to its neighbour", absf(absf(drot) - PI * 0.5) < 0.001)
	_check("joined house shares the ground floor level", absf(float(small.base) - float(big.base)) < 0.001)
	var sv: BuildingView = g.views.get(small.id)
	_check("joined house knows its neighbour's footprint", sv != null and sv.joins.size() >= 1)
	await _focus(Geo.v3(small.c, small.base + 2.5), 15.0)
	await _shot("5_joined_houses")
	# --- windows side by side merge (no errors, wide frame)
	small.windows = [{"side": 1, "u": 0.4, "f": 0, "kind": "window"}, {"side": 1, "u": 0.62, "f": 0, "kind": "window"}]
	g.refresh(small.id)
	await _frames(3)
	_check("side-by-side windows build", g.views.has(small.id))
	# --- roof over a ring of walls
	var ring := PackedVector2Array()
	var rc := Vector2(-14, 12)
	for k in 25:
		var a := TAU * k / 24.0
		ring.append(rc + Vector2(cos(a), sin(a)) * 3.2)
	var rw := g.add_wall(ring, 3.0, Catalog.STONE_COLORS[0], "stone", "glade")
	await _frames(3)
	var nb: int = g.data.buildings.size()
	var roof := g.add_roof_over_walls(rc, "gable", 1.1, Catalog.ROOF_COLORS[1])
	_check("roof tool roofs over a ring of walls", not roof.is_empty() and g.data.buildings.size() == nb + 1 and roof.get("roof_only", false))
	_check("a round ring gets a spire", not roof.is_empty() and roof.shape == "round")
	var sq := PackedVector2Array([Vector2(8, 14), Vector2(14, 14), Vector2(14, 18), Vector2(8, 18), Vector2(8, 14)])
	g.add_wall(Geo.resample(sq, 1.0), 2.6, Catalog.STONE_COLORS[1], "stone", "classic")
	var roof2 := g.add_roof_over_walls(Vector2(11, 16), "gable", 1.1, Catalog.ROOF_COLORS[0])
	_check("a square ring gets a gable roof", not roof2.is_empty() and roof2.shape == "rect")
	await _focus(Vector3(-2, 2.5, 15), 26.0)
	await _shot("6_roofs_on_walls")
	print("handles: %d failures" % fails)
	get_tree().quit()
