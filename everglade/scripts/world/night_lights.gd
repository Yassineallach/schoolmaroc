class_name NightLights
extends Node3D
## Warm local light from lanterns after dusk. A small pool of omni lights is
## moved to the lamps nearest the camera's focus, so lanterns light the walls,
## paths and grass around them and fade gradually into the dark (mobile
## friendly: a handful of real lights, no matter how many lamps exist).

const POOL := 6
# light height above the prop origin and reach, per lamp kind
const SOURCES := {
	"lantern": [2.45, 6.5], "paper_lantern": [2.1, 6.0], "stone_lantern": [1.0, 4.0],
	"wind_shrine": [1.6, 5.0], "fountain": [1.2, 3.5],
}

var glade: Glade
var rig: CameraRig
var day: DayCycle
var _lights: Array[OmniLight3D] = []
var _refresh := 0.0


func setup(g: Glade, r: CameraRig, d: DayCycle) -> void:
	glade = g
	rig = r
	day = d
	for i in POOL:
		var l := OmniLight3D.new()
		l.light_color = Color(1.0, 0.7, 0.42)
		l.shadow_enabled = false
		l.omni_attenuation = 1.6
		l.light_specular = 0.2
		l.visible = false
		add_child(l)
		_lights.append(l)


func _process(delta: float) -> void:
	if glade == null:
		return
	var night: float = day.night
	if night < 0.05:
		for l in _lights:
			l.visible = false
		return
	_refresh -= delta
	if _refresh <= 0.0:
		_refresh = 0.4
		_assign()
	var t := Time.get_ticks_msec() / 1000.0
	for i in _lights.size():
		var l := _lights[i]
		if l.visible:
			# a gentle candle flicker
			var f := 1.0 + 0.06 * sin(t * 7.3 + i * 1.7) + 0.04 * sin(t * 13.1 + i)
			l.light_energy = 1.4 * night * f * l.get_meta("scale", 1.0)


func _assign() -> void:
	var focus := rig.target
	var found: Array = []
	for p in glade.data.props:
		var src = SOURCES.get(p.kind)
		if src == null:
			continue
		var pos: Vector3 = p.p
		found.append([pos.distance_squared_to(focus), pos + Vector3.UP * src[0] * p.get("s", 1.0), src[1]])
	found.sort_custom(func(a, b): return a[0] < b[0])
	for i in _lights.size():
		var l := _lights[i]
		if i < found.size():
			l.position = found[i][1]
			l.omni_range = found[i][2]
			l.set_meta("scale", 1.0)
			l.visible = true
		else:
			l.visible = false
