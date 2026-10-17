extends Node
## Dev helper: wide views over the forest to the horizon, in several
## seasons and at night.  -- --horizon=/tmp/dir
var game: Game
var out := ""

# [template, season, time of day, yaw, pitch offset, distance]
const SHOTS := [
	["hamlet", 1, 0.42, 20.0, -0.55, 40.0],
	["meadow", 2, 0.45, 120.0, -0.6, 45.0],
	["village", 0, 0.4, 300.0, -0.5, 50.0],
	["ruins", 3, 0.42, 60.0, -0.55, 45.0],
	["ruins", 3, 0.02, 60.0, -0.55, 45.0],
]


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--horizon="):
			out = a.trim_prefix("--horizon=")
	DirAccess.make_dir_recursive_absolute(out)
	game = get_parent()
	_run.call_deferred()


func _run() -> void:
	for i in 60:
		await get_tree().process_frame
	var tpl := ""
	var k := 0
	var shots: Array = SHOTS.duplicate()
	if OS.get_environment("SHOTS") != "":
		shots.resize(int(OS.get_environment("SHOTS")))
	for s in shots:
		if s[0] != tpl:
			tpl = s[0]
			game.start_new(tpl)
		game.hud.visible = false
		if OS.get_environment("NOMSAA") != "":
			get_viewport().msaa_3d = Viewport.MSAA_DISABLED
		game.day.season = s[1]
		game.day.time_of_day = s[2]
		game.rig.focus_on(Vector3.ZERO, s[5])
		game.rig.yaw = deg_to_rad(s[3])
		game.rig.pitch_offset = s[4]
		game.rig.snap()
		for i in 240:
			await get_tree().process_frame
		if OS.get_environment("NODOF") != "":
			game.rig.process_mode = Node.PROCESS_MODE_DISABLED
			(game.rig.camera.attributes as CameraAttributesPractical).dof_blur_far_enabled = false
			for i in 3:
				await get_tree().process_frame
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(out.path_join("%d_%s.png" % [k, tpl]))
		k += 1
		game.rig.process_mode = Node.PROCESS_MODE_INHERIT
	get_tree().quit()
