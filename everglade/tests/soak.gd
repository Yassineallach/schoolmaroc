extends Node
## Dev helper: plays each template for a while with the wildlife on (the way
## a player sees it) and prints progress, to catch crashes that only show up
## after the glade has been running.  -- --soak[=seconds per template]
var game: Game
var seconds := 40.0


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--soak="):
			seconds = float(a.trim_prefix("--soak="))
	game = get_parent()
	_run.call_deferred()


func _run() -> void:
	for i in 30:
		await get_tree().process_frame
	for t in ["hamlet", "town", "ruins", "village", "meadow"]:
		print("soak: ", t)
		game.start_new(t)
		game.life.enabled = OS.get_environment("SOAK_NOLIFE") == ""
		if not game.life.enabled:
			game.life.clear()
		var t0 := Time.get_ticks_msec()
		var frames := 0
		while Time.get_ticks_msec() - t0 < seconds * 1000.0:
			await get_tree().process_frame
			frames += 1
		var prims := RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME)
		var draws := RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME)
		var vram := RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_VIDEO_MEM_USED) / 1048576
		print("soak: ", t, " ok, ", frames, " frames, ", prims, " triangles, ", draws, " draws, ", vram, " MB video, wildlife ", game.life.get("wildlife").size() if game.life.get("wildlife") != null else 0)
	print("soak: done")
	get_tree().quit()
