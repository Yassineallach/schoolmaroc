class_name CandleView
extends Node2D
## The candle. Its flame height is the score meter (Insight / target).

var flame: ColorRect
var mat: ShaderMaterial
const WICK := Vector2(0, -78)


func _ready() -> void:
	flame = ColorRect.new()
	flame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	flame.size = Vector2(70, 150)
	flame.position = WICK + Vector2(-35, -148)
	mat = ShaderMaterial.new()
	mat.shader = load("res://shaders/flame.gdshader")
	flame.material = mat
	add_child(flame)


func set_flame(height: float, gutter: float, flare: float) -> void:
	mat.set_shader_parameter("height", height)
	mat.set_shader_parameter("gutter", gutter)
	mat.set_shader_parameter("flare", flare)


func _draw() -> void:
	# Brass dish.
	draw_colored_polygon(Art.ellipse(Vector2(0, 6), 52, 14), Color(0.32, 0.22, 0.1))
	draw_colored_polygon(Art.ellipse(Vector2(0, 2), 48, 11), Color(0.6, 0.44, 0.2))
	draw_arc(Vector2(0, 2), 40, PI * 1.1, PI * 1.6, 12, Color(1, 0.85, 0.5, 0.6), 2.0, true)
	# Wax body with drips, lit from the flame side.
	var body := Rect2(-17, -76, 34, 78)
	draw_rect(body, Color("#E6D8BA"))
	draw_rect(Rect2(6, -76, 11, 78), Color(0.75, 0.66, 0.5, 0.55))
	for d in [[-12, -76, 18], [-2, -76, 30], [9, -76, 12]]:
		draw_rect(Rect2(d[0], d[1], 5, d[2]), Color("#EFE4CC"))
		draw_circle(Vector2(d[0] + 2.5, d[1] + d[2]), 3.0, Color("#EFE4CC"))
	draw_colored_polygon(Art.ellipse(Vector2(0, -76), 17, 5), Color("#F4EAD4"))
	draw_line(Vector2(0, -78), WICK + Vector2(0, -8), Art.INK, 2.0)
