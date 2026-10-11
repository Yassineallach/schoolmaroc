class_name BaseTool
extends Node3D
## Base class for every build tool. The Game routes single-finger input here.

signal options_changed

var game # Game (untyped to avoid a dependency cycle)
var glade: Glade
var tool_id := ""
var title := ""
var options: Dictionary = {}


func setup(g, gl: Glade) -> void:
	game = g
	glade = gl


## Array of option descriptors rendered by the HUD:
## {type:"choice", key, items:[{id,label,icon}]} | {type:"slider", key, label, min, max, step}
## | {type:"colors", key, colors:[Color]} | {type:"toggle", key, label, icon}
func option_defs() -> Array:
	return []


func set_option(key: String, value: Variant) -> void:
	options[key] = value
	options_changed.emit()


func activate() -> void:
	pass


func deactivate() -> void:
	cancel()


## Return true to own the drag (otherwise the camera pans).
func press(_screen: Vector2) -> bool:
	return false


func drag(_screen: Vector2) -> void:
	pass


func release(_screen: Vector2) -> void:
	pass


func tap(_screen: Vector2) -> void:
	pass


func cancel() -> void:
	pass


func hint() -> String:
	return ""


func process_hold(_delta: float) -> void:
	pass


# --- helpers -----------------------------------------------------------------
func camera() -> Camera3D:
	return game.rig.camera


func ground(screen: Vector2) -> Variant:
	var h := glade.pick(camera(), screen, 1)
	if h.is_empty():
		return null
	var p: Vector3 = h.point
	var c := glade.terrain.clamp_to_play(Vector2(p.x, p.z))
	return Vector3(c.x, glade.terrain.height_at_v(c), c.y)


func pick(screen: Vector2, mask := 0xF) -> Dictionary:
	return glade.pick(camera(), screen, mask)
