class_name SpellSVG
extends RefCounted

## Spell card art as SVG, rasterised at whatever size the card is shown.
## Three separate parts:
##   frame()  - the shared card: background, double border, corners,
##              numeral plaque and nameplate (no text)
##   ART      - each spell's emblem, drawn in the 200 x 300 card space
##   numeral and name text are drawn by SpellView with the game's font
## A card is frame + emblem; textures are cached per spell and pixel size.

const VIEW_W := 200.0
const VIEW_H := 300.0
## Where SpellView writes the text, in card units.
const NUMERAL_Y := 24.0
const NAME_Y := 266.0

const INK := "#2a2420"       # charcoal
const GOLD := "#c9a24a"      # antique gold
const IVORY := "#f3ead6"     # warm ivory
const PARCH := "#d9c7a3"     # muted parchment

## Arcana number for each spell (its place among the 22).
const NUMERAL := {
	"replay": 0, "clover": 1, "oracle": 2, "charge": 3, "summon": 4, "etch": 5, "chimera": 6,
	"forge": 7, "glaze": 8, "windfall": 9, "fortune": 10, "ascend": 11, "purge": 12, "mirror": 13,
	"barter": 14, "gild": 15, "petrify": 16, "kindle": 17, "bramble": 18, "bloom": 19,
	"conjure": 20, "shade": 21,
}
const ROMAN := ["0", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII",
	"XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX", "XXI"]

static var _cache := {}


static func has_art(id: String) -> bool:
	return ART.has(id)


static func roman(id: String) -> String:
	return ROMAN[NUMERAL.get(id, 0)]


## The card for `id` as a texture `px_w` pixels wide.
static func texture(id: String, px_w: int) -> ImageTexture:
	var key := "%s@%d" % [id, px_w]
	if not _cache.has(key):
		var img := Image.new()
		img.load_svg_from_string(svg(id), px_w / VIEW_W)
		_cache[key] = ImageTexture.create_from_image(img)
	return _cache[key]


static func svg(id: String) -> String:
	return '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="300" viewBox="0 0 200 300">%s%s</svg>' \
		% [frame(), ART.get(id, "")]


## The shared card frame, everything except the emblem and the text.
static func frame() -> String:
	var g := GOLD
	return "".join([
		# card body with a faint inner glow behind the emblem
		'<rect x="0" y="0" width="200" height="300" rx="12" fill="%s"/>' % INK,
		'<circle cx="100" cy="142" r="78" fill="%s" opacity="0.05"/>' % IVORY,
		# thin double border
		'<rect x="7" y="7" width="186" height="286" rx="8" fill="none" stroke="%s" stroke-width="1.6"/>' % g,
		'<rect x="12" y="12" width="176" height="276" rx="5" fill="none" stroke="%s" stroke-width="0.7" opacity="0.8"/>' % g,
		# corner ornaments: a small diamond and a dot in each corner
		_corner(20, 20), _corner(180, 20), _corner(20, 280), _corner(180, 280),
		# numeral plaque breaking the top border
		'<path d="M84 12 L116 12 L112 34 L88 34 Z" fill="%s" stroke="%s" stroke-width="1"/>' % [INK, g],
		'<line x1="91" y1="31" x2="109" y2="31" stroke="%s" stroke-width="0.5" opacity="0.6"/>' % g,
		# divider above the nameplate
		'<line x1="30" y1="244" x2="86" y2="244" stroke="%s" stroke-width="0.7"/>' % g,
		'<line x1="114" y1="244" x2="170" y2="244" stroke="%s" stroke-width="0.7"/>' % g,
		'<path d="M100 239 L105 244 L100 249 L95 244 Z" fill="%s"/>' % g,
		# nameplate
		'<rect x="34" y="253" width="132" height="26" rx="3" fill="%s" stroke="%s" stroke-width="1"/>' % [INK, g],
		'<rect x="37" y="256" width="126" height="20" rx="2" fill="none" stroke="%s" stroke-width="0.5" opacity="0.6"/>' % g,
	])


static func _corner(x: float, y: float) -> String:
	return '<path d="M%s %s l4 4 l-4 4 l-4 -4 Z" fill="none" stroke="%s" stroke-width="0.9"/><circle cx="%s" cy="%s" r="1" fill="%s"/>' \
		% [x, y - 4, GOLD, x, y, GOLD]


# ---------------------------------------------------------------- emblems
# Each is drawn around the card's centre (100, 142), inside about r = 75.

const ART := {
	# 0 Replay: an arrow circling back on itself around an hourglass -
	# copy the last spell again.
	"replay": "" \
		+ '<circle cx="100" cy="142" r="70" fill="none" stroke="#c9a24a" stroke-width="0.6" opacity="0.5"/>' \
		+ '<circle cx="100" cy="142" r="64" fill="none" stroke="#c9a24a" stroke-width="0.6" stroke-dasharray="1 5" opacity="0.8"/>' \
		+ '<path d="M100 88 A54 54 0 1 1 46 142" fill="none" stroke="#f3ead6" stroke-width="3" stroke-linecap="round"/>' \
		+ '<path d="M37 152 L46 140 L56 151" fill="none" stroke="#f3ead6" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>' \
		+ '<path d="M100 88 A54 54 0 0 0 46 142" fill="none" stroke="#f3ead6" stroke-width="1" stroke-dasharray="2 4" opacity="0.6"/>' \
		+ '<path d="M84 112 L116 112 L104 142 L116 172 L84 172 L96 142 Z" fill="none" stroke="#c9a24a" stroke-width="2" stroke-linejoin="round"/>' \
		+ '<path d="M90 118 L110 118 L100 136 Z" fill="#c9a24a"/>' \
		+ '<path d="M100 152 L110 166 L90 166 Z" fill="#c9a24a" opacity="0.55"/>' \
		+ '<line x1="80" y1="112" x2="120" y2="112" stroke="#c9a24a" stroke-width="2.5" stroke-linecap="round"/>' \
		+ '<line x1="80" y1="172" x2="120" y2="172" stroke="#c9a24a" stroke-width="2.5" stroke-linecap="round"/>' \
		+ '<circle cx="100" cy="72" r="2" fill="#c9a24a"/><circle cx="170" cy="142" r="2" fill="#c9a24a"/>' \
		+ '<circle cx="100" cy="212" r="2" fill="#c9a24a"/><circle cx="30" cy="142" r="2" fill="#c9a24a"/>',
}
