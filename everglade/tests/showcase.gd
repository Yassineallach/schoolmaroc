extends Node
## Dev helper: renders the three reference showcase glades from an overview
## and an eye-level angle.  -- --showcase=/tmp/dir
var game: Game
var out := ""

const SHOTS := {
	"ruins": [[Vector3(0, 0, -2), 30.0, 20.0, -0.15], [Vector3(0, 1.5, -3), 12.0, 8.0, -0.32], [Vector3(0, 0, 0), 60.0, 30.0, -0.55]],
	"town": [[Vector3(0, 0, -1), 30.0, 15.0, -0.1], [Vector3(0, 1.0, -1), 9.0, 20.0, -0.28]],
	"village": [[Vector3(0, 0, -2), 32.0, 10.0, -0.15], [Vector3(0, 0.5, -3), 15.0, 345.0, -0.3], [Vector3(0, 2, 0), 30.0, 190.0, -0.4]],
}


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--showcase="):
			out = a.trim_prefix("--showcase=")
	DirAccess.make_dir_recursive_absolute(out)
	game = get_parent()
	_run.call_deferred()


func _shot(n: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(n + ".png"))


func _run() -> void:
	for i in 60:
		await get_tree().process_frame
	for tpl in SHOTS:
		var t0 := Time.get_ticks_msec()
		game.start_new(tpl)
		print("built ", tpl, " in ", Time.get_ticks_msec() - t0, " ms, props ", game.glade.data.props.size())
		game.hud.visible = false
		var k := 0
		for s in SHOTS[tpl]:
			game.rig.focus_on(s[0], s[1])
			game.rig.yaw = deg_to_rad(s[2])
			game.rig.pitch_offset = s[3]
			game.rig.snap()
			for i in 50:
				await get_tree().process_frame
			await _shot("%s_%d" % [tpl, k])
			k += 1
		game.rig.pitch_offset = 0.0
	get_tree().quit()
