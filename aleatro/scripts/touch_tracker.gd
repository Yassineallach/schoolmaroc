class_name TouchTracker
extends RefCounted

## Turns raw press/move/release events on one control into tap, hold and
## drag gestures.

const DRAG_DIST := 14.0
const HOLD_TIME := 0.45

var pressing := false
var dragging := false
var held := false
var _start := Vector2.ZERO
var _timer := 0.0


## Returns "tap", "drag_start", "drag", "drag_end" or "".
func handle(event: InputEvent) -> String:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			pressing = true
			dragging = false
			held = false
			_start = event.global_position
			_timer = 0.0
			return ""
		if not pressing:
			return ""
		pressing = false
		if dragging:
			dragging = false
			return "drag_end"
		return "" if held else "tap"
	if event is InputEventMouseMotion and pressing:
		if not dragging and not held and event.global_position.distance_to(_start) > DRAG_DIST:
			dragging = true
			return "drag_start"
		if dragging:
			return "drag"
	return ""


## Call every frame; true once when a press becomes a hold.
func tick(delta: float) -> bool:
	if pressing and not dragging and not held:
		_timer += delta
		if _timer >= HOLD_TIME:
			held = true
			return true
	return false
