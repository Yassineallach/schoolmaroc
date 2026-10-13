class_name UIIcon
extends Control
## Hand-drawn style vector icons rendered with CanvasItem primitives, so the
## UI stays crisp at any phone resolution without bitmap assets.

const INK := Color(0.32, 0.26, 0.22)
const STONE := Color(0.80, 0.77, 0.71)
const ROOF := Color(0.84, 0.45, 0.35)
const WOOD := Color(0.66, 0.47, 0.30)
const LEAF := Color(0.48, 0.70, 0.36)
const WATER := Color(0.45, 0.70, 0.86)
const SUN := Color(0.98, 0.78, 0.30)
const PAPER := Color(0.98, 0.95, 0.88)
const DIRT := Color(0.80, 0.66, 0.48)

@export var icon := "": set = set_icon
var tint := Color.WHITE
var texture: Texture2D: set = set_texture


func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	custom_minimum_size = Vector2(44, 44)


func set_icon(v: String) -> void:
	icon = v
	queue_redraw()


func set_texture(t: Texture2D) -> void:
	texture = t
	queue_redraw()


func _p(x: float, y: float) -> Vector2:
	var s := minf(size.x, size.y)
	var o := (size - Vector2(s, s)) * 0.5
	return o + Vector2(x, y) * s


func _w(v: float) -> float:
	return v * minf(size.x, size.y)


func poly(pts: Array, col: Color, outline := true) -> void:
	var arr := PackedVector2Array()
	for p in pts:
		arr.append(_p(p.x, p.y))
	draw_colored_polygon(arr, col * tint)
	if outline:
		arr.append(arr[0])
		draw_polyline(arr, INK * tint, _w(0.045), true)


func line(pts: Array, col := INK, width := 0.05) -> void:
	var arr := PackedVector2Array()
	for p in pts:
		arr.append(_p(p.x, p.y))
	draw_polyline(arr, col * tint, _w(width), true)


func circle(c: Vector2, r: float, col: Color, outline := true) -> void:
	draw_circle(_p(c.x, c.y), _w(r), col * tint)
	if outline:
		draw_arc(_p(c.x, c.y), _w(r), 0, TAU, 32, INK * tint, _w(0.045), true)


func rect(x: float, y: float, w: float, h: float, col: Color, outline := true) -> void:
	poly([Vector2(x, y), Vector2(x + w, y), Vector2(x + w, y + h), Vector2(x, y + h)], col, outline)


func _draw() -> void:
	if texture:
		var s := minf(size.x, size.y)
		draw_texture_rect(texture, Rect2((size - Vector2(s, s)) * 0.5, Vector2(s, s)), false)
		return
	match icon:
		"hand":
			poly([Vector2(0.3, 0.9), Vector2(0.25, 0.55), Vector2(0.22, 0.4), Vector2(0.3, 0.38), Vector2(0.36, 0.5), Vector2(0.36, 0.2), Vector2(0.44, 0.17), Vector2(0.5, 0.2), Vector2(0.52, 0.15), Vector2(0.6, 0.16), Vector2(0.62, 0.22), Vector2(0.7, 0.22), Vector2(0.74, 0.3), Vector2(0.74, 0.65), Vector2(0.66, 0.9)], PAPER)
		"wall":
			for row in 3:
				for c in 3:
					var off := 0.0 if row % 2 == 0 else 0.13
					rect(0.1 + c * 0.27 - off + (0.13 if row % 2 == 1 and c == 0 else 0.0), 0.3 + row * 0.2, 0.25 if not (row % 2 == 1 and c == 0) else 0.12, 0.18, STONE)
			rect(0.12, 0.18, 0.18, 0.12, STONE)
			rect(0.42, 0.18, 0.18, 0.12, STONE)
			rect(0.72, 0.18, 0.18, 0.12, STONE)
		"wall_rendered":
			rect(0.1, 0.3, 0.8, 0.6, Color(0.93, 0.88, 0.76))
			for p in [Vector2(0.1, 0.3), Vector2(0.1, 0.5), Vector2(0.1, 0.7), Vector2(0.75, 0.4), Vector2(0.75, 0.6)]:
				rect(p.x, p.y, 0.15, 0.17, STONE)
			rect(0.4, 0.62, 0.16, 0.12, STONE)
			for x in [0.1, 0.42, 0.74]:
				rect(x, 0.12, 0.16, 0.18, STONE)
		"building", "house":
			rect(0.22, 0.48, 0.56, 0.4, PAPER)
			poly([Vector2(0.12, 0.52), Vector2(0.5, 0.16), Vector2(0.88, 0.52)], ROOF)
			rect(0.44, 0.64, 0.13, 0.24, WOOD)
			rect(0.62, 0.56, 0.1, 0.1, SUN)
			rect(0.62, 0.22, 0.08, 0.16, STONE)
		"tower":
			rect(0.32, 0.42, 0.36, 0.48, STONE)
			poly([Vector2(0.24, 0.45), Vector2(0.5, 0.06), Vector2(0.76, 0.45)], Color(0.45, 0.58, 0.8))
			rect(0.45, 0.56, 0.1, 0.14, SUN)
		"fence":
			for x in [0.18, 0.5, 0.82]:
				poly([Vector2(x - 0.06, 0.88), Vector2(x - 0.06, 0.3), Vector2(x, 0.22), Vector2(x + 0.06, 0.3), Vector2(x + 0.06, 0.88)], WOOD)
			rect(0.08, 0.42, 0.84, 0.08, WOOD)
			rect(0.08, 0.64, 0.84, 0.08, WOOD)
		"fence_ornate":
			for x in [0.14, 0.86]:
				rect(x - 0.08, 0.2, 0.16, 0.7, STONE)
				rect(x - 0.1, 0.14, 0.2, 0.08, STONE)
			rect(0.22, 0.3, 0.56, 0.06, WOOD)
			rect(0.22, 0.78, 0.56, 0.06, WOOD)
			circle(Vector2(0.5, 0.56), 0.13, WOOD, false)
		"path":
			poly([Vector2(0.32, 0.95), Vector2(0.4, 0.62), Vector2(0.6, 0.38), Vector2(0.56, 0.08), Vector2(0.68, 0.08), Vector2(0.76, 0.4), Vector2(0.58, 0.64), Vector2(0.56, 0.95)], DIRT)
		"cobble":
			for p in [Vector2(0.3, 0.3), Vector2(0.6, 0.28), Vector2(0.45, 0.52), Vector2(0.25, 0.7), Vector2(0.7, 0.62), Vector2(0.5, 0.82)]:
				circle(p, 0.13, STONE)
		"paved":
			for r in 3:
				for c in 3:
					rect(0.1 + c * 0.27 + (0.06 if r == 1 else 0.0), 0.12 + r * 0.27, 0.23, 0.23, STONE)
		"stones":
			for p in [Vector2(0.3, 0.78), Vector2(0.55, 0.52), Vector2(0.38, 0.26), Vector2(0.7, 0.18)]:
				circle(p, 0.11, STONE)
			line([Vector2(0.05, 0.6), Vector2(0.95, 0.4)], WATER, 0.06)
		"details", "window":
			rect(0.22, 0.14, 0.56, 0.72, SUN)
			line([Vector2(0.5, 0.14), Vector2(0.5, 0.86)])
			line([Vector2(0.22, 0.48), Vector2(0.78, 0.48)])
			rect(0.16, 0.84, 0.68, 0.08, STONE)
		"door":
			poly([Vector2(0.28, 0.92), Vector2(0.28, 0.35), Vector2(0.35, 0.18), Vector2(0.5, 0.12), Vector2(0.65, 0.18), Vector2(0.72, 0.35), Vector2(0.72, 0.92)], WOOD)
			circle(Vector2(0.62, 0.58), 0.04, INK, false)
		"dormer":
			poly([Vector2(0.05, 0.9), Vector2(0.5, 0.35), Vector2(0.95, 0.9)], ROOF)
			rect(0.36, 0.42, 0.28, 0.3, PAPER)
			poly([Vector2(0.3, 0.46), Vector2(0.5, 0.22), Vector2(0.7, 0.46)], ROOF)
			rect(0.44, 0.52, 0.12, 0.14, SUN)
		"chimney":
			poly([Vector2(0.05, 0.92), Vector2(0.5, 0.5), Vector2(0.95, 0.92)], ROOF)
			rect(0.56, 0.3, 0.18, 0.4, STONE)
			circle(Vector2(0.62, 0.2), 0.07, Color(0.9, 0.9, 0.9))
			circle(Vector2(0.74, 0.08), 0.05, Color(0.9, 0.9, 0.9))
		"roof", "gable":
			poly([Vector2(0.08, 0.7), Vector2(0.5, 0.22), Vector2(0.92, 0.7)], ROOF)
			rect(0.2, 0.7, 0.6, 0.2, PAPER)
		"hip":
			poly([Vector2(0.08, 0.7), Vector2(0.35, 0.3), Vector2(0.65, 0.3), Vector2(0.92, 0.7)], ROOF)
			rect(0.2, 0.7, 0.6, 0.2, PAPER)
		"flat":
			rect(0.2, 0.42, 0.6, 0.48, STONE)
			for x in [0.2, 0.42, 0.64]:
				rect(x, 0.26, 0.16, 0.16, STONE)
		"windrise":
			rect(0.15, 0.15, 0.7, 0.7, PAPER)
			rect(0.15, 0.58, 0.7, 0.27, STONE)
			line([Vector2(0.15, 0.58), Vector2(0.85, 0.58)], Color(0.95, 0.74, 0.3), 0.06)
			line([Vector2(0.5, 0.15), Vector2(0.5, 0.58)], WOOD.darkened(0.45), 0.06)
			line([Vector2(0.15, 0.58), Vector2(0.5, 0.15)], WOOD.darkened(0.45), 0.05)
		"lakeside":
			rect(0.18, 0.4, 0.64, 0.5, PAPER)
			rect(0.18, 0.78, 0.64, 0.12, STONE.darkened(0.3))
			poly([Vector2(0.06, 0.44), Vector2(0.2, 0.36), Vector2(0.5, 0.22), Vector2(0.8, 0.36), Vector2(0.94, 0.44), Vector2(0.8, 0.42), Vector2(0.2, 0.42)], Color(0.3, 0.32, 0.38))
			rect(0.08, 0.14, 0.1, 0.3, PAPER)
			rect(0.82, 0.14, 0.1, 0.3, PAPER)
			rect(0.06, 0.12, 0.14, 0.04, Color(0.3, 0.32, 0.38))
			rect(0.8, 0.12, 0.14, 0.04, Color(0.3, 0.32, 0.38))
			rect(0.42, 0.56, 0.16, 0.16, Color(0.36, 0.24, 0.16))
		"grand":
			rect(0.43, 0.6, 0.14, 0.3, WOOD)
			circle(Vector2(0.5, 0.4), 0.34, LEAF)
		"cone":
			poly([Vector2(0.26, 0.6), Vector2(0.5, 0.08), Vector2(0.74, 0.6)], Color(0.45, 0.58, 0.8))
			rect(0.32, 0.6, 0.36, 0.3, STONE)
		"nature", "forest", "broadleaf":
			rect(0.45, 0.6, 0.1, 0.3, WOOD)
			circle(Vector2(0.5, 0.42), 0.28, LEAF)
			circle(Vector2(0.38, 0.5), 0.12, LEAF.lightened(0.15), false)
		"golden", "blossom":
			var crown := Color(0.98, 0.78, 0.3) if icon == "golden" else Color(0.98, 0.84, 0.9)
			rect(0.45, 0.6, 0.1, 0.3, WOOD)
			circle(Vector2(0.5, 0.42), 0.28, crown)
			circle(Vector2(0.38, 0.5), 0.12, crown.lightened(0.2), false)
		"lavender":
			for x in [0.3, 0.5, 0.7]:
				line([Vector2(x, 0.92), Vector2(x, 0.4)], LEAF.darkened(0.2), 0.05)
				for k in 4:
					circle(Vector2(x, 0.2 + k * 0.08), 0.05, Color(0.62, 0.5, 0.9), false)
		"pines":
			rect(0.45, 0.72, 0.1, 0.2, WOOD)
			poly([Vector2(0.2, 0.75), Vector2(0.5, 0.1), Vector2(0.8, 0.75)], Color(0.28, 0.5, 0.36))
		"bushes":
			circle(Vector2(0.35, 0.62), 0.2, LEAF)
			circle(Vector2(0.62, 0.58), 0.24, LEAF.darkened(0.1))
			circle(Vector2(0.62, 0.5), 0.05, ROOF, false)
		"flowers":
			line([Vector2(0.5, 0.92), Vector2(0.5, 0.5)], LEAF.darkened(0.2), 0.06)
			for i in 5:
				var a := TAU * i / 5.0
				circle(Vector2(0.5, 0.35) + Vector2(cos(a), sin(a)) * 0.13, 0.1, Color(0.96, 0.62, 0.74))
			circle(Vector2(0.5, 0.35), 0.08, SUN)
		"ferns":
			for k in 5:
				var a := lerpf(-1.1, 1.1, k / 4.0)
				line([Vector2(0.5, 0.9), Vector2(0.5 + sin(a) * 0.36, 0.9 - cos(a) * 0.62)], LEAF.darkened(0.05 * k), 0.07)
		"rocks":
			poly([Vector2(0.1, 0.85), Vector2(0.2, 0.5), Vector2(0.45, 0.35), Vector2(0.7, 0.45), Vector2(0.88, 0.85)], STONE)
			poly([Vector2(0.22, 0.52), Vector2(0.45, 0.36), Vector2(0.62, 0.42), Vector2(0.4, 0.5)], LEAF, false)
		"decor", "lantern":
			rect(0.46, 0.2, 0.08, 0.72, WOOD)
			rect(0.54, 0.24, 0.2, 0.06, WOOD)
			rect(0.58, 0.32, 0.16, 0.2, SUN)
			poly([Vector2(0.56, 0.32), Vector2(0.66, 0.24), Vector2(0.76, 0.32)], INK)
		"terrain", "raise":
			poly([Vector2(0.05, 0.85), Vector2(0.35, 0.35), Vector2(0.55, 0.55), Vector2(0.7, 0.3), Vector2(0.95, 0.85)], LEAF)
			if icon == "raise":
				line([Vector2(0.5, 0.25), Vector2(0.5, 0.05)], INK, 0.06)
				line([Vector2(0.4, 0.14), Vector2(0.5, 0.05), Vector2(0.6, 0.14)], INK, 0.06)
		"cliff":
			poly([Vector2(0.05, 0.9), Vector2(0.05, 0.62), Vector2(0.3, 0.62), Vector2(0.36, 0.3), Vector2(0.78, 0.3), Vector2(0.84, 0.62), Vector2(0.95, 0.62), Vector2(0.95, 0.9)], STONE)
			rect(0.34, 0.24, 0.46, 0.08, LEAF)
			rect(0.05, 0.56, 0.25, 0.07, LEAF)
			line([Vector2(0.45, 0.45), Vector2(0.7, 0.45)], STONE.darkened(0.3), 0.03)
		"stack":
			rect(0.15, 0.62, 0.7, 0.26, LEAF.darkened(0.15))
			rect(0.28, 0.38, 0.44, 0.24, LEAF)
			rect(0.4, 0.16, 0.2, 0.22, LEAF.lightened(0.15))
		"lower":
			poly([Vector2(0.05, 0.4), Vector2(0.3, 0.4), Vector2(0.5, 0.75), Vector2(0.7, 0.4), Vector2(0.95, 0.4), Vector2(0.95, 0.9), Vector2(0.05, 0.9)], LEAF)
			line([Vector2(0.5, 0.08), Vector2(0.5, 0.3)], INK, 0.06)
			line([Vector2(0.4, 0.2), Vector2(0.5, 0.3), Vector2(0.6, 0.2)], INK, 0.06)
		"smooth":
			poly([Vector2(0.05, 0.9), Vector2(0.05, 0.6), Vector2(0.3, 0.45), Vector2(0.7, 0.45), Vector2(0.95, 0.6), Vector2(0.95, 0.9)], LEAF)
		"flatten":
			rect(0.05, 0.55, 0.9, 0.35, LEAF)
			line([Vector2(0.1, 0.38), Vector2(0.9, 0.38)], INK, 0.06)
		"water", "fill":
			poly([Vector2(0.5, 0.08), Vector2(0.78, 0.55), Vector2(0.72, 0.78), Vector2(0.5, 0.9), Vector2(0.28, 0.78), Vector2(0.22, 0.55)], WATER)
			if icon == "fill":
				rect(0.05, 0.7, 0.9, 0.22, DIRT)
		"eraser":
			poly([Vector2(0.15, 0.62), Vector2(0.55, 0.22), Vector2(0.85, 0.52), Vector2(0.45, 0.92)], Color(0.95, 0.66, 0.66))
			poly([Vector2(0.15, 0.62), Vector2(0.32, 0.45), Vector2(0.62, 0.75), Vector2(0.45, 0.92)], PAPER)
		"undo", "redo":
			var flip := icon == "redo"
			var pts: Array = []
			for i in 13:
				var a := lerpf(PI * 1.1, PI * 2.2, i / 12.0)
				var p := Vector2(0.5 + cos(a) * 0.3, 0.58 + sin(a) * 0.3)
				pts.append(Vector2(1.0 - p.x, p.y) if flip else p)
			line(pts, INK, 0.09)
			var tip: Vector2 = pts[0]
			var arrow := [tip + Vector2(-0.14 if not flip else 0.14, -0.04), tip, tip + Vector2(0.02 if not flip else -0.02, -0.16)]
			line(arrow, INK, 0.09)
		"sun":
			circle(Vector2(0.5, 0.5), 0.2, SUN)
			for i in 8:
				var a := TAU * i / 8.0
				line([Vector2(0.5, 0.5) + Vector2(cos(a), sin(a)) * 0.3, Vector2(0.5, 0.5) + Vector2(cos(a), sin(a)) * 0.42], INK, 0.06)
		"moon":
			circle(Vector2(0.5, 0.5), 0.32, Color(0.95, 0.92, 0.75))
			circle(Vector2(0.64, 0.4), 0.26, Color(0, 0, 0, 0), false)
			draw_circle(_p(0.66, 0.38), _w(0.24), Color(0.3, 0.36, 0.55) * tint)
		"camera":
			rect(0.1, 0.3, 0.8, 0.55, PAPER)
			rect(0.3, 0.2, 0.2, 0.1, PAPER)
			circle(Vector2(0.5, 0.57), 0.17, WATER)
		"menu", "home":
			rect(0.25, 0.48, 0.5, 0.42, PAPER)
			poly([Vector2(0.12, 0.52), Vector2(0.5, 0.15), Vector2(0.88, 0.52)], ROOF)
		"settings":
			for i in 8:
				var a := TAU * i / 8.0
				circle(Vector2(0.5, 0.5) + Vector2(cos(a), sin(a)) * 0.3, 0.09, STONE, false)
			circle(Vector2(0.5, 0.5), 0.3, STONE)
			circle(Vector2(0.5, 0.5), 0.11, PAPER)
		"season":
			poly([Vector2(0.5, 0.1), Vector2(0.8, 0.45), Vector2(0.5, 0.9), Vector2(0.2, 0.45)], Color(0.92, 0.6, 0.3))
			line([Vector2(0.5, 0.2), Vector2(0.5, 0.95)], INK, 0.05)
		"close":
			line([Vector2(0.25, 0.25), Vector2(0.75, 0.75)], INK, 0.1)
			line([Vector2(0.75, 0.25), Vector2(0.25, 0.75)], INK, 0.1)
		"check":
			line([Vector2(0.2, 0.52), Vector2(0.42, 0.74), Vector2(0.82, 0.28)], INK, 0.1)
		"trash":
			rect(0.25, 0.3, 0.5, 0.6, Color(0.95, 0.7, 0.68))
			rect(0.18, 0.2, 0.64, 0.1, Color(0.95, 0.7, 0.68))
			rect(0.4, 0.1, 0.2, 0.1, Color(0.95, 0.7, 0.68))
		"plus":
			line([Vector2(0.5, 0.2), Vector2(0.5, 0.8)], INK, 0.12)
			line([Vector2(0.2, 0.5), Vector2(0.8, 0.5)], INK, 0.12)
		"minus":
			line([Vector2(0.2, 0.5), Vector2(0.8, 0.5)], INK, 0.12)
		"rotl", "rotr":
			var pts2: Array = []
			for i in 13:
				var a := lerpf(-PI * 0.2, PI * 1.3, i / 12.0)
				var p := Vector2(0.5 + cos(a) * 0.3, 0.5 + sin(a) * 0.3)
				pts2.append(Vector2(1.0 - p.x, p.y) if icon == "rotr" else p)
			line(pts2, INK, 0.08)
			var t2: Vector2 = pts2[0]
			line([t2 + Vector2(-0.12 if icon == "rotl" else 0.12, 0.0), t2, t2 + Vector2(0.0, 0.14)], INK, 0.08)
		"ruler":
			poly([Vector2(0.1, 0.7), Vector2(0.7, 0.1), Vector2(0.9, 0.3), Vector2(0.3, 0.9)], SUN)
			for i in 4:
				var b := Vector2(0.25 + i * 0.13, 0.55 - i * 0.13)
				line([b, b + Vector2(0.06, 0.06)], INK, 0.04)
		"plaster":
			rect(0.15, 0.15, 0.7, 0.7, Color(0.96, 0.92, 0.83))
		"timber":
			rect(0.15, 0.15, 0.7, 0.7, Color(0.96, 0.92, 0.83))
			line([Vector2(0.15, 0.5), Vector2(0.85, 0.5)], WOOD.darkened(0.3), 0.08)
			line([Vector2(0.5, 0.15), Vector2(0.5, 0.85)], WOOD.darkened(0.3), 0.08)
			line([Vector2(0.15, 0.85), Vector2(0.5, 0.5)], WOOD.darkened(0.3), 0.08)
		"stone":
			rect(0.15, 0.15, 0.34, 0.22, STONE)
			rect(0.51, 0.15, 0.34, 0.22, STONE)
			rect(0.15, 0.39, 0.5, 0.22, STONE)
			rect(0.67, 0.39, 0.18, 0.22, STONE)
			rect(0.15, 0.63, 0.3, 0.22, STONE)
			rect(0.47, 0.63, 0.38, 0.22, STONE)
		"ivy":
			for p in [Vector2(0.3, 0.75), Vector2(0.45, 0.55), Vector2(0.35, 0.35), Vector2(0.55, 0.2), Vector2(0.65, 0.45)]:
				circle(p, 0.1, LEAF)
		"pets", "sheep":
			circle(Vector2(0.45, 0.5), 0.26, PAPER)
			circle(Vector2(0.75, 0.45), 0.12, INK, false)
			line([Vector2(0.35, 0.72), Vector2(0.35, 0.9)], INK, 0.07)
			line([Vector2(0.58, 0.72), Vector2(0.58, 0.9)], INK, 0.07)
		"photo":
			rect(0.1, 0.3, 0.8, 0.55, PAPER)
			circle(Vector2(0.5, 0.57), 0.17, WATER)
		"play":
			poly([Vector2(0.3, 0.2), Vector2(0.8, 0.5), Vector2(0.3, 0.8)], ROOF)
		_:
			circle(Vector2(0.5, 0.5), 0.3, STONE)
