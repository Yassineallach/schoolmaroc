class_name QuerentView
extends Node2D
## The Querent across the table: a silhouette lit from below by the candle.

var kind := "curious"
var lean := 0.0      # 0..1, leans in as Insight rises
var recoil := 0.0    # 0..1, flinches when the Shadow acts
var stand := 0.0     # 0..1, rises at defeat
var puppet := ""     # Major id cast as a shadow puppet on the wall
var puppet_alpha := 0.0
var puppet_dance := 0.0
var time := 0.0


func _process(delta: float) -> void:
	time += delta
	queue_redraw()


func _draw() -> void:
	if puppet != "" and puppet_alpha > 0.0:
		var pc := Vector2(590, 160) + Vector2(sin(time * 3.0), cos(time * 2.3)) * 8.0 * puppet_dance
		draw_set_transform(pc, sin(time * 2.0) * 0.1 * puppet_dance, Vector2.ONE)
		Art.major_emblem(self, Vector2.ZERO, 190.0, puppet, Color(0, 0, 0, 0.55 * puppet_alpha), Color(0, 0, 0, 0.55 * puppet_alpha))
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	var base := Vector2(360, 300) + Vector2(0, -60 * stand + 6 * lean - 8 * recoil)
	var s := 1.0 + 0.05 * lean - 0.04 * recoil
	draw_set_transform(base, 0.0, Vector2(s, s))
	var ink := Color(0.035, 0.027, 0.022)
	var shoulders := PackedVector2Array([Vector2(-150, 0), Vector2(-128, -70), Vector2(-62, -104),
		Vector2(-30, -112), Vector2(30, -112), Vector2(62, -104), Vector2(128, -70), Vector2(150, 0)])
	draw_colored_polygon(shoulders, ink)
	draw_rect(Rect2(-22, -140, 44, 40), ink)
	match kind:
		"curious":
			draw_circle(Vector2(0, -170), 42, ink)
			draw_colored_polygon(PackedVector2Array([Vector2(-78, -192), Vector2(78, -192), Vector2(48, -206), Vector2(40, -238), Vector2(-40, -238), Vector2(-48, -206)]), ink)
		"troubled":
			draw_circle(Vector2(0, -168), 40, ink)
			draw_colored_polygon(PackedVector2Array([Vector2(-70, -100), Vector2(-64, -190), Vector2(-30, -228), Vector2(30, -228), Vector2(64, -190), Vector2(70, -100)]), ink)
		"twin":
			draw_circle(Vector2(-40, -166), 36, ink)
			draw_circle(Vector2(44, -162), 36, ink)
			draw_rect(Rect2(10, -140, 44, 40), ink)
			draw_colored_polygon(PackedVector2Array([Vector2(-76, -170), Vector2(-40, -214), Vector2(-4, -170)]), ink)
			draw_colored_polygon(PackedVector2Array([Vector2(8, -166), Vector2(44, -210), Vector2(80, -166)]), ink)
	# Underlight: warm edge along the lower outline, fading upward.
	var glow := PackedVector2Array([Vector2(-150, 0), Vector2(-128, -70), Vector2(-62, -104), Vector2(62, -104), Vector2(128, -70), Vector2(150, 0)])
	var cols := PackedColorArray([Color(1, 0.62, 0.3, 0.32), Color(1, 0.6, 0.3, 0.08), Color(1, 0.6, 0.3, 0.0),
		Color(1, 0.6, 0.3, 0.0), Color(1, 0.6, 0.3, 0.08), Color(1, 0.62, 0.3, 0.32)])
	draw_polygon(glow, cols)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
