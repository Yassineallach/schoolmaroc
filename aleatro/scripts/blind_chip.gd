class_name BlindChip
extends Control

## A spinning, hovering token for a blind. The spin advances in discrete
## frames at Anim.FPS so it reads like a sprite-sheet animation. Blinds with
## art (assets/blinds/<id>.png: "small", "big" or a boss id) spin that chip;
## others get a drawn token in their colour.

const FRAMES := 12

var color := Color.WHITE
var art: Texture2D = null
var spin := true  # false: a still chip, for lists
var _start := Anim.now()
var _phase := randf() * TAU


func _init(c: Color = Color.WHITE, s: float = 56.0, id: String = "") -> void:
	color = c
	set_blind(id)
	size = Vector2(s, s)
	custom_minimum_size = size
	mouse_filter = Control.MOUSE_FILTER_IGNORE


## Show the chip art for blind `id` ("" or an id without art: drawn token).
func set_blind(id: String) -> void:
	var path := "res://assets/blinds/%s.png" % id
	art = load(path) if id != "" and ResourceLoader.exists(path) else null


func _process(_delta: float) -> void:
	if spin and is_visible_in_tree():
		queue_redraw()


func _draw() -> void:
	var frame := int(floor(Anim.FPS * (Anim.now() - _start))) % FRAMES if spin else 0
	var squash := maxf(absf(cos(PI * frame / FRAMES)), 0.14)
	var r := size.x / 2.0 - 4.0
	var lift := Anim.lift(_phase, 1.0)
	var c := size / 2.0 + Vector2(0, -2.0 * lift)
	var face := color if frame < FRAMES / 2 else color.darkened(0.12)
	draw_set_transform(c + Vector2(2, 4) * lift, 0, Vector2(squash, 1))
	draw_circle(Vector2.ZERO, r, Color(0, 0, 0, 0.3))
	draw_set_transform(c, 0, Vector2(squash, 1))
	if art != null:
		var rr := size.x / 2.0 - 2.0
		var tint := Color.WHITE if frame < FRAMES / 2 else Color(0.88, 0.88, 0.88)
		draw_texture_rect(art, Rect2(-rr, -rr, 2 * rr, 2 * rr), false, tint)
		draw_set_transform(Vector2.ZERO, 0, Vector2.ONE)
		return
	draw_circle(Vector2.ZERO, r, face.darkened(0.4))
	draw_circle(Vector2.ZERO, r * 0.84, face)
	for i in 8:
		var a := TAU * i / 8.0
		draw_circle(Vector2(cos(a), sin(a)) * r * 0.92, r * 0.09, Color(1, 1, 1, 0.85))
	draw_arc(Vector2.ZERO, r * 0.58, 0, TAU, 24, face.lightened(0.45), 3.0)
	draw_circle(Vector2.ZERO, r * 0.22, face.lightened(0.3))
	draw_set_transform(Vector2.ZERO, 0, Vector2.ONE)
