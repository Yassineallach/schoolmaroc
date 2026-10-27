extends SceneTree

## Renders a 512x512 store / Play Games icon from the game's own pieces: the
## title's swirl, a soft spotlight, a fanned Ace and King, and the Jester charm
## in front with a Chroma shine. Everything that matters sits inside the
## middle 80%, which survives Play's rounded mask.
##   xvfb-run godot --rendering-driver opengl3 --resolution 512x512 \
##       -s tools/play_games/store_icon.gd
## Writes tools/play_games/properties/icon_512.png.

const OUT := "res://tools/play_games/properties/icon_512.png"
const S := 512.0


func _initialize() -> void:
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	var c := Control.new()
	c.size = Vector2(S, S)
	root.add_child(c)
	# the title's red and blue swirl
	var bg := ColorRect.new()
	bg.size = c.size
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/splash.gdshader")
	m.set_shader_parameter("time", 13.0)
	m.set_shader_parameter("vort_speed", 0.4)
	m.set_shader_parameter("colour_1", Color("fe5f55"))
	m.set_shader_parameter("colour_2", Color("009dff"))
	bg.material = m
	c.add_child(bg)
	# a spotlight behind the cards and a darker rim, so they pop
	var light := TextureRect.new()
	light.texture = _radial(Color(1.0, 0.85, 0.42, 0.85), Color(1.0, 0.6, 0.3, 0.0))
	light.size = c.size
	c.add_child(light)
	var rim := TextureRect.new()
	rim.texture = _radial(Color(0, 0, 0, 0.0), Color(0.02, 0.03, 0.05, 0.7), 0.55)
	rim.size = c.size
	c.add_child(rim)
	# the hand: King and Ace fanned behind the Jester
	var ace := CardView.new({"rank": 14, "suit": 0, "id": -1, "seal": "golden"})
	var king := CardView.new({"rank": 13, "suit": 1, "id": -1, "ed": "foil"})
	for pair in [[king, -26.0, Vector2(-112, 10)], [ace, 24.0, Vector2(112, 14)]]:
		var v: CardView = pair[0]
		v.float_amount = 0.0
		v.scale = Vector2.ONE * 1.75
		v.rotation_degrees = pair[1]
		v.position = Vector2(S, S) / 2.0 - v.size / 2.0 + pair[2]
		c.add_child(v)
	# Chroma's shine without its edition tag: icons carry no text
	var joker := CharmView.new("jester")
	joker.float_amount = 0.0
	joker.scale = Vector2.ONE * 1.95
	joker.position = Vector2(S, S) / 2.0 - joker.size / 2.0 + Vector2(0, -4)
	joker._ensure_material().set_shader_parameter("edition", Data.EDITIONS["chroma"].shader)
	c.add_child(joker)
	_shoot.call_deferred()


## A soft round gradient from `inner` (centre) to `outer` (corners).
func _radial(inner: Color, outer: Color, start := 0.0) -> Texture2D:
	var g := Gradient.new()
	g.set_color(0, inner)
	g.set_color(1, outer)
	g.set_offset(0, start)
	var t := GradientTexture2D.new()
	t.gradient = g
	t.fill = GradientTexture2D.FILL_RADIAL
	t.fill_from = Vector2(0.5, 0.5)
	t.fill_to = Vector2(1.0, 0.5)
	t.width = int(S)
	t.height = int(S)
	return t


func _shoot() -> void:
	for i in 12:
		await process_frame
	var img := root.get_texture().get_image()
	img.convert(Image.FORMAT_RGB8)
	img.save_png(ProjectSettings.globalize_path(OUT))
	print("saved ", OUT, " ", img.get_size())
	quit()
