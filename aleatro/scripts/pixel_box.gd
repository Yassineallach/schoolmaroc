@tool
class_name PixelBox
extends StyleBox

## A box with stair-stepped "pixel" corners, an optional embossed lower lip,
## a drop shadow and an outline. Used for every panel, button, card and charm.
## Cards set `rounded` for smooth, anti-aliased round corners instead.

@export var color := Color.WHITE
@export var step := 3.0  # size of one corner "pixel"
@export var emboss := 0.0  # depth of the darker lip under the box
@export var shadow := false
@export var shadow_offset := Vector2(3, 5)
@export var shadow_color := Color(0, 0, 0, 0.3)
@export var outline := 0.0
@export var outline_color := Color(1, 1, 1, 0.8)
@export var pressed := false  # sink the face into the emboss lip
@export var rounded := false  # smooth round corners (radius 3 * step) instead of pixel steps


func _init(c: Color = Color.WHITE, s: float = 3.0, e: float = 0.0, sh: bool = false) -> void:
	color = c
	step = s
	emboss = e
	shadow = sh
	set_content_margin_all(12)


static func outline_points(rect: Rect2, s: float, round_corners := false) -> PackedVector2Array:
	if round_corners:
		return round_points(rect, 3.0 * s)
	var x0 := rect.position.x
	var y0 := rect.position.y
	var x1 := rect.end.x
	var y1 := rect.end.y
	s = minf(s, minf(rect.size.x, rect.size.y) / 8.0)
	return PackedVector2Array([
		Vector2(x0, y0 + 3 * s), Vector2(x0 + s, y0 + 3 * s), Vector2(x0 + s, y0 + s), Vector2(x0 + 3 * s, y0 + s), Vector2(x0 + 3 * s, y0),
		Vector2(x1 - 3 * s, y0), Vector2(x1 - 3 * s, y0 + s), Vector2(x1 - s, y0 + s), Vector2(x1 - s, y0 + 3 * s), Vector2(x1, y0 + 3 * s),
		Vector2(x1, y1 - 3 * s), Vector2(x1 - s, y1 - 3 * s), Vector2(x1 - s, y1 - s), Vector2(x1 - 3 * s, y1 - s), Vector2(x1 - 3 * s, y1),
		Vector2(x0 + 3 * s, y1), Vector2(x0 + 3 * s, y1 - s), Vector2(x0 + s, y1 - s), Vector2(x0 + s, y1 - 3 * s), Vector2(x0, y1 - 3 * s),
	])


## The outline of a rectangle with round corners of radius `r`.
static func round_points(rect: Rect2, r: float) -> PackedVector2Array:
	r = minf(r, minf(rect.size.x, rect.size.y) / 2.0)
	var pts := PackedVector2Array()
	var centres := [Vector2(rect.end.x - r, rect.position.y + r), Vector2(rect.end.x - r, rect.end.y - r),
		Vector2(rect.position.x + r, rect.end.y - r), Vector2(rect.position.x + r, rect.position.y + r)]
	for k in 4:
		for i in 7:
			var a := -PI / 2 + (k + i / 6.0) * PI / 2
			pts.append(centres[k] + Vector2(cos(a), sin(a)) * r)
	return pts


func _draw(to_canvas_item: RID, rect: Rect2) -> void:
	var face := rect
	face.size.y -= emboss
	var sink := emboss * 0.75 if pressed else 0.0
	if shadow and color.a > 0.01:
		var sr := rect
		sr.position += shadow_offset * (0.4 if pressed else 1.0)
		_poly(to_canvas_item, outline_points(sr, step, rounded), Color(shadow_color, shadow_color.a * color.a))
	if emboss > 0.0:
		var er := face
		er.position.y += emboss
		_poly(to_canvas_item, outline_points(er, step, rounded), color.darkened(0.4))
	face.position.y += sink
	var pts := outline_points(face, step, rounded)
	_poly(to_canvas_item, pts, color)
	if outline > 0.0:
		var loop := pts.duplicate()
		loop.append(pts[0])
		RenderingServer.canvas_item_add_polyline(to_canvas_item, loop, PackedColorArray([outline_color]), outline, rounded)


func _poly(ci: RID, pts: PackedVector2Array, c: Color) -> void:
	if c.a <= 0.0:
		return
	RenderingServer.canvas_item_add_polygon(ci, pts, PackedColorArray([c]))
	if rounded:
		# polygons are not anti-aliased: a thin smooth edge in the same colour softens the curve
		var loop := pts.duplicate()
		loop.append(pts[0])
		RenderingServer.canvas_item_add_polyline(ci, loop, PackedColorArray([c]), 1.0, true)
