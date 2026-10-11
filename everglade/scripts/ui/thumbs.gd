class_name Thumbs
extends Node
## Renders little 3D previews of props for the decoration pickers.

signal ready_thumb(kind: String, tex: Texture2D)

const SIZE := 128

var _cache: Dictionary = {}
var _queue: Array[String] = []
var _busy := false
var _vp: SubViewport
var _cam: Camera3D
var _holder: Node3D


func _ready() -> void:
	_vp = SubViewport.new()
	_vp.size = Vector2i(SIZE, SIZE)
	_vp.transparent_bg = true
	_vp.own_world_3d = true
	_vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
	_vp.msaa_3d = Viewport.MSAA_4X
	add_child(_vp)
	var env := Environment.new()
	env.background_mode = Environment.BG_CLEAR_COLOR
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.9, 0.9, 1.0)
	env.ambient_light_energy = 0.7
	var we := WorldEnvironment.new()
	we.environment = env
	_vp.add_child(we)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-50, 35, 0)
	sun.light_energy = 1.1
	_vp.add_child(sun)
	_cam = Camera3D.new()
	_cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	_vp.add_child(_cam)
	_holder = Node3D.new()
	_vp.add_child(_holder)


func get_thumb(kind: String) -> Texture2D:
	if _cache.has(kind):
		return _cache[kind]
	if not _queue.has(kind):
		_queue.append(kind)
	if not _busy:
		_run()
	return null


func _run() -> void:
	_busy = true
	while not _queue.is_empty():
		var kind: String = _queue.pop_front()
		if not ModelLib.has_model(kind):
			continue
		for c in _holder.get_children():
			c.free()
		var m := ModelLib.instance(kind)
		_holder.add_child(m)
		var aabb: AABB = ModelLib.merged(kind).aabb
		var center := aabb.get_center()
		var extent := maxf(aabb.size.length(), 0.3)
		_cam.size = extent * 0.95
		var dir := Vector3(0.9, 0.75, 1.1).normalized()
		_cam.look_at_from_position(center + dir * extent * 3.0, center, Vector3.UP)
		_vp.render_target_update_mode = SubViewport.UPDATE_ONCE
		await RenderingServer.frame_post_draw
		var img := _vp.get_texture().get_image()
		if img:
			var tex := ImageTexture.create_from_image(img)
			_cache[kind] = tex
			ready_thumb.emit(kind, tex)
	_busy = false
