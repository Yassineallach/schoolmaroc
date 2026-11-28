class_name TableView
extends Node2D
## Chalk positions on the cloth, Shadow ink stains, and the drag hover outline.

const LABELS: Array[String] = ["PAST", "PRESENT", "FUTURE"]
const HINTS: Array[String] = ["counts twice", "+2 Gravity", "half, returns"]
var centers: Array[Vector2] = []
var slot_size := Vector2(156, 250)
var blocked: Array = []
var upcoming: Array = []
var hover := -1
var underline: Array[float] = [0.0, 0.0, 0.0]
var stain_grow: Array[float] = [0.0, 0.0, 0.0]
var show_slots := true
var arcana_centers: Array[Vector2] = []
var arcana_visible := false
var time := 0.0


func _process(delta: float) -> void:
	time += delta
	if not blocked.is_empty() or not upcoming.is_empty():
		queue_redraw()


func slot_rect(p: int) -> Rect2:
	return Rect2(centers[p] - slot_size / 2.0, slot_size)


func _draw() -> void:
	if arcana_visible:
		for c in arcana_centers:
			_dashed_rect(Rect2(c - Vector2(33, 52), Vector2(66, 104)), Color(Art.CHALK, 0.22), 1.5)
	if not show_slots:
		return
	for p in 3:
		var r := slot_rect(p)
		_dashed_rect(r, Art.CHALK if hover != p else Color(Art.GOLD, 0.9), 2.0 if hover != p else 3.0)
		var lc := Vector2(centers[p].x, r.end.y + 24)
		Art.text(self, Art.font_sc, lc, LABELS[p], 21, Art.CHALK)
		Art.text(self, Art.font, lc + Vector2(0, 19), HINTS[p], 15, Color(Art.CHALK, 0.32))
		if underline[p] > 0.0:
			var w := 96.0 * underline[p]
			draw_line(lc + Vector2(-48, 7), lc + Vector2(-48 + w, 7), Color(Art.BONE, 0.85), 2.5)
	for it in upcoming:
		var p := int(it["pos"])
		Art.ink_blob(self, centers[p], slot_size.x * 0.42, 40 + p, Color(Art.INK, 0.4), time)
		Art.text(self, Art.font, centers[p] + Vector2(0, 6), "the Shadow", 22, Color(Art.BONE, 0.55))
		Art.text(self, Art.font, centers[p] + Vector2(0, 30), "reaches here next", 18, Color(Art.BONE, 0.45))
	for p in blocked:
		var g: float = stain_grow[p] if stain_grow[p] > 0.0 else 1.0
		Art.ink_blob(self, centers[p], slot_size.x * 0.62 * g, 40 + p, Color(Art.INK, 0.94), time * 0.6)
		Art.text(self, Art.font_sc, centers[p] + Vector2(0, 8), "ECLIPSED", 24, Color(Art.BONE, 0.5 * g))


func _dashed_rect(r: Rect2, col: Color, w: float) -> void:
	var pts := [r.position, Vector2(r.end.x, r.position.y), r.end, Vector2(r.position.x, r.end.y), r.position]
	for i in 4:
		var a: Vector2 = pts[i]
		var b: Vector2 = pts[i + 1]
		var n := int(a.distance_to(b) / 14.0)
		for k in n:
			if k % 2 == 0:
				draw_line(a.lerp(b, float(k) / n), a.lerp(b, float(k + 1) / n), col, w)
