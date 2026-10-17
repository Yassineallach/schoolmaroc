extends Node
## Dev helper: where the frame goes in a built-up glade (draw calls,
## triangles by part of the scene, script time).  -- --perfstats=town
var game: Game
var template := "town"


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--perfstats="):
			template = a.trim_prefix("--perfstats=")   # "town,scripts" also times each script
	game = get_parent()
	_run.call_deferred()


static func _tris(mesh: Mesh) -> int:
	var t := 0
	if mesh == null:
		return 0
	for s in mesh.get_surface_count():
		var arr := mesh.surface_get_arrays(s)
		var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX] if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
		t += idx.size() / 3 if idx.size() > 0 else (arr[Mesh.ARRAY_VERTEX] as PackedVector3Array).size() / 3
	return t


func _walk(n: Node, bucket: String, out: Dictionary) -> void:
	var b := bucket
	if b == "" and n.get_parent() == game.glade:
		b = String(n.name)
	if n is MeshInstance3D and (n as MeshInstance3D).visible:
		var mi := n as MeshInstance3D
		var t := _tris(mi.mesh)
		var key := b if b != "" else String(n.get_parent().name) + "/" + String(n.name)
		if not out.has(key):
			out[key] = Vector3i.ZERO
		out[key] += Vector3i(t, 1, t if mi.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_OFF else 0)
	elif n is MultiMeshInstance3D and (n as MultiMeshInstance3D).visible:
		var mm := (n as MultiMeshInstance3D).multimesh
		if mm and mm.mesh:
			var t2 := _tris(mm.mesh) * mm.visible_instance_count if mm.visible_instance_count >= 0 else _tris(mm.mesh) * mm.instance_count
			var key2 := b if b != "" else String(n.get_parent().name) + "/" + String(n.name)
			if not out.has(key2):
				out[key2] = Vector3i.ZERO
			out[key2] += Vector3i(t2, 1, t2 if (n as GeometryInstance3D).cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_OFF else 0)
	for c in n.get_children():
		_walk(c, b, out)


func _run() -> void:
	for i in 60:
		await get_tree().process_frame
	game.start_new(template.split(",")[0])
	for i in 120:
		await get_tree().process_frame
	var proc := 0.0
	var phys := 0.0
	for i in 120:
		await get_tree().process_frame
		proc += Performance.get_monitor(Performance.TIME_PROCESS)
		phys += Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS)
	print("PERF process %.2f ms  physics %.2f ms (avg/frame)" % [proc / 120.0 * 1000.0, phys / 120.0 * 1000.0])
	print("PERF draw calls %d  primitives %d  objects %d" % [
		RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
		RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME),
		RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME)])
	print("PERF nodes %d  video mem %.1f MB" % [Performance.get_monitor(Performance.OBJECT_NODE_COUNT),
		Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0])
	var out := {}
	_walk(game.glade, "", out)
	var keys := out.keys()
	keys.sort_custom(func(a, b): return out[a].x > out[b].x)
	var total := 0
	for k in keys:
		total += out[k].x
	print("PERF scene triangles (all, in or out of view) %d" % total)
	for k in keys.slice(0, 25):
		print("PERF  %-34s tris %8d  meshes %4d  shadow-tris %8d" % [k, out[k].x, out[k].y, out[k].z])
	# scripts that run every frame
	var procs := {}
	for n in get_tree().root.find_children("*", "", true, false):
		if n.is_processing() and n.get_script():
			var sn: String = (n.get_script() as Script).resource_path.get_file()
			procs[sn] = procs.get(sn, 0) + 1
	print("PERF processing scripts ", procs)
	if not template.ends_with(",scripts"):
		get_tree().quit()
		return
	# script time per frame with each kind of script paused in turn
	var base := await _proc_ms(40)
	print("PERF base process %.2f ms" % base)
	for sn in procs:
		var nodes: Array = []
		for nd in get_tree().root.find_children("*", "", true, false):
			if nd.is_processing() and nd.get_script() and (nd.get_script() as Script).resource_path.get_file() == sn and nd != self:
				nodes.append(nd)
		for nd in nodes:
			nd.set_process(false)
		var t := await _proc_ms(40)
		for nd in nodes:
			nd.set_process(true)
		print("PERF  without %-18s %8.2f ms  (saves %.2f)" % [sn, t, base - t])
	get_tree().quit()


## Mean wall time of a frame (run headless, that is the scripts and engine
## work without the GPU), taking the median of a few batches.
func _proc_ms(frames: int) -> float:
	var batches: Array[float] = []
	for b in 5:
		await get_tree().process_frame
		var t0 := Time.get_ticks_usec()
		for i in frames:
			await get_tree().process_frame
		batches.append((Time.get_ticks_usec() - t0) / 1000.0 / frames)
	batches.sort()
	return batches[2]
