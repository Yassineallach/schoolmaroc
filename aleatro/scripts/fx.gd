class_name Fx
extends RefCounted

## Balatro's Card:start_materialize: the dissolve (card_fx.gdshader) run
## backwards, so a new card burns into view rimmed in its type's colour.

const CARD_FX := preload("res://shaders/card_fx.gdshader")

# the spark colours per kind of card, from the palette
const RARITY := Palette.RARITY
const SPELL := Palette.VIOLET
const RUNE := Palette.GLOW
const OMEN := Palette.INDIGO
const PACK := Palette.ROSE
const VOUCHER := Palette.COPPER
const PLAYING := Palette.JADE  # anything else


## Burn `view` into view over `time` seconds in `colours` (one or two).
static func materialize(view: Control, colours: Array, time := 0.6) -> void:
	var m: ShaderMaterial
	if view.has_method("_ensure_material"):
		m = view._ensure_material()
	else:
		m = view.material as ShaderMaterial
		if m == null:
			m = ShaderMaterial.new()
			m.shader = CARD_FX
			var sz := view.size if view.size != Vector2.ZERO else view.custom_minimum_size
			m.set_shader_parameter("size", sz)
			view.material = m
	m.set_shader_parameter("burn_colour_1", colours[0])
	m.set_shader_parameter("burn_colour_2", colours[1] if colours.size() > 1 else Color(0, 0, 0, 0))
	m.set_shader_parameter("dissolve_seed", randf() * 3000.0)
	m.set_shader_parameter("dissolve", 1.0)
	var tw := view.create_tween()
	tw.tween_method(func(v): m.set_shader_parameter("dissolve", v), 1.0, 0.0, time)
	# a shine laid over the art (packs, Omens) fades in with it
	for c in view.get_children():
		if c is CanvasItem and c.material != null:
			c.modulate.a = 0.0
			view.create_tween().tween_property(c, "modulate:a", 1.0, time)


## The colour start_materialize gives a charm, spell or shop item.
static func colour_for(kind: String, id = null) -> Color:
	match kind:
		"charm":
			return RARITY[clampi(Data.charm_def(id).get("rarity", 0), 0, 3)]
		"spell":
			var d := Data.spell_def(id)
			return RUNE if d.has("rune") else OMEN if d.get("omen", false) else SPELL
		"pack":
			return PACK
		"voucher":
			return VOUCHER
	return PLAYING
