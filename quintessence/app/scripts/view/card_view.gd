class_name CardView
extends Node2D
## One card on the table. Draws its own candle-cast shadow, then the woodcut face.

const SIZE := Vector2(156, 250)
static var light_origin := Vector2(110, 470)

var card: Dictionary = {}
var major := ""
var marked := false:
	set(v):
		marked = v
		queue_redraw()
var lit := false:
	set(v):
		lit = v
		queue_redraw()
var dim := 0.0:
	set(v):
		dim = v
		queue_redraw()
var ash := 0.0:
	set(v):
		ash = v
		queue_redraw()
var lift := 0.0
var _last := Transform2D()


func card_id() -> int:
	return int(card.get("id", -1))


func _process(_delta: float) -> void:
	var t := global_transform
	if t != _last:
		_last = t
		queue_redraw()


func contains(global_point: Vector2) -> bool:
	return Rect2(-SIZE / 2.0, SIZE).has_point(to_local(global_point))


func _draw() -> void:
	var away := global_position - light_origin
	var reach := clampf(away.length() * 0.018, 4.0, 13.0) + lift * 10.0
	var off := (away.normalized() * reach).rotated(-global_rotation) / maxf(global_scale.x, 0.01)
	draw_rect(Rect2(-SIZE / 2.0 + off, SIZE), Color(0, 0, 0, 0.42 - lift * 0.1))
	draw_rect(Rect2(-SIZE / 2.0 + off * 0.5, SIZE), Color(0, 0, 0, 0.18))
	if major != "":
		Art.major_card(self, SIZE, major, lit)
	elif card.is_empty():
		Art.card_back(self, SIZE)
	else:
		Art.minor_card(self, SIZE, card)
	if lit:
		draw_rect(Rect2(-SIZE / 2.0, SIZE).grow(3), Art.GOLD, false, 4.0)
	if marked:
		draw_rect(Rect2(-SIZE / 2.0, SIZE), Color(Art.INK, 0.35))
		var k := SIZE.x * 0.3
		draw_line(Vector2(-k, -k), Vector2(k, k), Art.INK, 12.0)
		draw_line(Vector2(-k, k), Vector2(k, -k), Art.INK, 12.0)
		draw_line(Vector2(-k, -k), Vector2(k, k), Art.VERMILION, 5.0)
		draw_line(Vector2(-k, k), Vector2(k, -k), Art.VERMILION, 5.0)
	if dim > 0.0:
		draw_rect(Rect2(-SIZE / 2.0, SIZE), Color(Art.INK, dim * 0.65))
	if ash > 0.0:
		draw_rect(Rect2(-SIZE / 2.0, SIZE), Color(0.32, 0.3, 0.28, clampf(ash * 1.2, 0, 1)))
		var edge := SIZE.y * (0.5 - ash)
		draw_line(Vector2(-SIZE.x / 2, edge), Vector2(SIZE.x / 2, edge), Color(1.0, 0.55, 0.15, 1.0 - ash), 5.0)
