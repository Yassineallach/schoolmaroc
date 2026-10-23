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
	return NUMERAL.has(id)


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
		% [frame(), emblem(id)]


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
# Each spell's emblem, drawn around the card's centre (100, 142) within
# about r = 75: ivory for the main sign, gold for structure and accents.

const C := Vector2(100, 142)


static func emblem(id: String) -> String:
	match id:
		"replay":  # an arrow circling back round an hourglass: cast the last spell again
			return _backdrop() \
				+ _arc(100, 142, 54, -90, 180, IVORY, 3) \
				+ _path("M37 152 L46 140 L56 151", IVORY, 3) \
				+ _arc(100, 142, 54, 180, 270, IVORY, 1, 'stroke-dasharray="2 4" opacity="0.6"') \
				+ _path("M84 112 L116 112 L104 142 L116 172 L84 172 L96 142 Z", GOLD, 2) \
				+ _fill("M90 118 L110 118 L100 136 Z", GOLD) + _fill("M100 152 L110 166 L90 166 Z", GOLD, 0.55) \
				+ _line(80, 112, 120, 112, GOLD, 2.5) + _line(80, 172, 120, 172, GOLD, 2.5)
		"clover":  # a four-leaf clover in a ring of seven stars: make cards Lucky
			var leaves := ""
			for a in [0, 90, 180, 270]:
				leaves += '<g transform="rotate(%d 100 136)">%s</g>' % [a, _path("M100 136 C 84 120 84 98 100 104 C 116 98 116 120 100 136 Z", IVORY, 2.5)]
				leaves += '<g transform="rotate(%d 100 136)">%s</g>' % [a, _line(100, 132, 100, 112, GOLD, 1)]
			var stars := ""
			for k in 7:
				var ang := deg_to_rad(-90 + k * 360.0 / 7)
				stars += _star(100 + cos(ang) * 64, 142 + sin(ang) * 64, 4, 1.6, GOLD)
			return _ring(100, 142, 70, GOLD, 0.6, 'opacity="0.5"') + stars + leaves \
				+ _path("M100 136 C 102 156 108 170 118 182", IVORY, 2.5) + _circle(100, 136, 3, GOLD, 0, GOLD)
		"oracle":  # a crescent over an open eye, two rune stones beneath: create Runes
			return _backdrop() \
				+ _fill("M86 76 A20 20 0 1 0 114 76 A15 15 0 1 1 86 76 Z", IVORY) \
				+ _path("M56 132 Q100 92 144 132 Q100 172 56 132 Z", IVORY, 2.5) \
				+ _circle(100, 132, 15, GOLD, 2) + _circle(100, 132, 6, GOLD, 0, GOLD) \
				+ _line(100, 104, 100, 96, GOLD, 1.2) + _line(78, 110, 73, 103, GOLD, 1.2) + _line(122, 110, 127, 103, GOLD, 1.2) \
				+ _hex(78, 186, 13, IVORY) + _path("M73 180 L83 192 M83 180 L73 192", GOLD, 1.6) \
				+ _hex(122, 186, 13, IVORY) + _path("M122 178 L122 194 M116 184 L122 178 L128 184", GOLD, 1.6)
		"charge":  # a lightning bolt splitting a charged ring: make cards Charged (+Mult)
			var ticks := ""
			for k in 16:
				var ang := deg_to_rad(k * 22.5)
				ticks += _line(100 + cos(ang) * 50, 142 + sin(ang) * 50, 100 + cos(ang) * (58 if k % 2 else 64), 142 + sin(ang) * (58 if k % 2 else 64), GOLD, 1.4)
			return _ring(100, 142, 70, GOLD, 0.6, 'opacity="0.5"') + ticks + _ring(100, 142, 44, GOLD, 1.5) \
				+ _fill("M108 82 L78 148 L98 148 L88 202 L124 128 L104 128 Z", IVORY) \
				+ _plus(58, 106, GOLD) + _plus(142, 178, GOLD)
		"summon":  # two cards rising out of a magic circle: create Spells
			return _ellipse(100, 186, 62, 18, GOLD, 1.6) + _ellipse(100, 186, 48, 12, GOLD, 0.8, 'stroke-dasharray="3 3"') \
				+ _card(66, 92, -12, IVORY) + _card(110, 84, 12, IVORY) \
				+ _path("M100 176 L100 72", GOLD, 0.8, 'stroke-dasharray="2 5" opacity="0.7"') \
				+ _star(100, 62, 9, 3.5, GOLD) + _star(60, 168, 4, 1.6, GOLD) + _star(142, 168, 4, 1.6, GOLD)
		"etch":  # a chisel cutting a chip into a stone tablet: make cards Etched (+Chips)
			var notches := ""
			for k in 8:
				var ang := deg_to_rad(k * 45)
				notches += _line(96 + cos(ang) * 16, 150 + sin(ang) * 16, 96 + cos(ang) * 24, 150 + sin(ang) * 24, GOLD, 3)
			return _backdrop() \
				+ _path("M58 92 Q100 76 142 92 L142 198 L58 198 Z", IVORY, 2.5) \
				+ _circle(96, 150, 24, GOLD, 2) + notches + _circle(96, 150, 10, GOLD, 1.5) \
				+ _path("M128 70 L150 92 L120 122 L112 114 Z", IVORY, 2, "", PARCH) + _line(116, 118, 106, 128, IVORY, 3) \
				+ _star(76, 112, 3, 1.2, GOLD) + _star(118, 132, 3, 1.2, GOLD)
		"chimera":  # all four suits bound into one star: make a card Wild
			var lines := _path("M100 86 L156 142 L100 198 L44 142 Z", GOLD, 1.2) + _ring(100, 142, 26, GOLD, 1.2)
			return _backdrop() + lines \
				+ _suit("spade", 100, 86, 13) + _suit("heart", 156, 142, 13) + _suit("club", 100, 198, 13) + _suit("diamond", 44, 142, 13) \
				+ _star(100, 142, 18, 7, IVORY)
		"forge":  # a hammer over an anvil, sparks flying: make a card Iron
			var sparks := ""
			for a in [-150, -120, -60, -30]:
				var ang := deg_to_rad(a)
				sparks += _line(100 + cos(ang) * 22, 128 + sin(ang) * 22, 100 + cos(ang) * 36, 128 + sin(ang) * 36, GOLD, 1.6)
			return _backdrop() + sparks \
				+ _path("M56 140 L144 140 L144 150 Q122 152 118 164 L126 184 L74 184 L82 164 Q78 152 56 150 Z", IVORY, 2.5, "", INK) \
				+ _line(56, 145, 40, 142, IVORY, 2.5) + _line(70, 190, 130, 190, GOLD, 2) \
				+ '<g transform="rotate(-35 118 96)">' + _path("M104 84 L132 84 L132 100 L104 100 Z", GOLD, 2, "", INK) + _line(118, 100, 118, 132, GOLD, 3) + '</g>'
		"glaze":  # a cut-glass gem catching light, one crack running through: make a card Glass
			return _backdrop() \
				+ _path("M100 76 L136 112 L100 208 L64 112 Z", IVORY, 2.5) \
				+ _path("M64 112 L136 112 M82 94 L100 112 L118 94 M100 112 L100 208 M82 112 L100 208 L118 112", GOLD, 1.2) \
				+ _path("M118 140 L110 152 L116 160 L108 172", PARCH, 1.4) \
				+ _line(46, 82, 70, 98, IVORY, 1.2, 'opacity="0.7"') + _line(40, 96, 62, 106, IVORY, 1.2, 'opacity="0.5"') \
				+ _star(144, 84, 5, 2, GOLD)
		"windfall":  # two coins, one doubling the other, under falling gold: double your money
			var rain := ""
			for k in 7:
				var x := 46 + k * 18
				rain += _circle(x, 82 + (k % 3) * 10, 3, GOLD, 1.2)
			return _ring(100, 142, 70, GOLD, 0.6, 'opacity="0.5"') + rain \
				+ _circle(86, 150, 30, IVORY, 2.5) + _circle(86, 150, 22, IVORY, 1) \
				+ _circle(118, 136, 30, GOLD, 2.5, "", INK) + _circle(118, 136, 22, GOLD, 1) \
				+ _path("M110 128 L126 128 M118 120 L118 152 M110 144 Q118 152 126 144", GOLD, 2.5)
		"fortune":  # an eight-spoked wheel, one segment lit: a chance at an edition
			var spokes := ""
			for k in 8:
				var ang := deg_to_rad(k * 45)
				spokes += _line(100 + cos(ang) * 12, 142 + sin(ang) * 12, 100 + cos(ang) * 58, 142 + sin(ang) * 58, GOLD, 1.6)
			return _ring(100, 142, 70, GOLD, 0.6, 'opacity="0.5"') \
				+ _fill("M100 142 L100 84 A58 58 0 0 1 141 101 Z", GOLD, 0.35) \
				+ _ring(100, 142, 58, IVORY, 3) + _ring(100, 142, 48, GOLD, 1) + spokes + _ring(100, 142, 12, IVORY, 2.5) \
				+ _star(100, 70, 6, 2.4, IVORY) + _star(172, 142, 4, 1.6, GOLD) + _star(28, 142, 4, 1.6, GOLD)
		"ascend":  # a stair of three cards climbing to a star: raise a card's rank
			return _backdrop() \
				+ _card(52, 160, 0, PARCH, 0.75) + _card(80, 132, 0, IVORY, 0.85) + _card(108, 104, 0, IVORY) \
				+ _path("M60 92 L60 70 M52 78 L60 70 L68 78", GOLD, 2.5) \
				+ _path("M64 210 L148 210", GOLD, 1) + _star(150, 82, 7, 3, GOLD)
		"purge":  # a flame consuming two cards: destroy cards
			return _backdrop() \
				+ _card(70, 140, -18, PARCH, 0.8) + _card(104, 140, 16, PARCH, 0.8) \
				+ _path("M100 74 C 120 100 140 118 134 152 C 130 180 112 196 100 196 C 82 196 66 182 66 156 C 66 136 82 128 84 108 C 92 120 92 132 96 136 C 104 116 100 96 100 74 Z", IVORY, 2.5, "", INK) \
				+ _path("M100 128 C 112 144 116 160 110 174 C 106 184 94 184 90 174 C 86 162 94 152 100 128 Z", GOLD, 1.5, "", GOLD)
		"mirror":  # a card and its reflection across a mirror's axis: copy one card onto another
			return _ellipse(100, 142, 62, 76, GOLD, 1.6) + _ellipse(100, 142, 56, 70, GOLD, 0.6) \
				+ _line(100, 70, 100, 214, GOLD, 1, 'stroke-dasharray="3 4"') \
				+ _card(48, 112, 0, IVORY) + _card(112, 112, 0, IVORY, 0.55) \
				+ _suit("heart", 66, 140, 10) + '<g opacity="0.55">' + _suit("heart", 130, 140, 10) + '</g>' \
				+ _path("M84 196 L116 196 M108 190 L116 196 L108 202", GOLD, 1.6)
		"barter":  # balanced scales: a charm against a pile of coins - sell value as money
			return _backdrop() \
				+ _line(100, 78, 100, 196, IVORY, 2.5) + _line(84, 198, 116, 198, IVORY, 2.5) + _circle(100, 76, 4, GOLD, 0, GOLD) \
				+ _line(52, 96, 148, 96, IVORY, 2.5) \
				+ _path("M52 96 L38 140 M52 96 L66 140", GOLD, 1) + _path("M148 96 L134 140 M148 96 L162 140", GOLD, 1) \
				+ _path("M34 140 Q52 156 70 140 Z", IVORY, 2) + _path("M130 140 Q148 156 166 140 Z", IVORY, 2) \
				+ _star(52, 126, 9, 4, GOLD) \
				+ _circle(142, 132, 5, GOLD, 1.4, "", INK) + _circle(154, 132, 5, GOLD, 1.4, "", INK) + _circle(148, 124, 5, GOLD, 1.4, "", INK)
		"gild":  # the alchemical sun over a card running with gold: make a card Gilded
			# the card is drawn larger here, gold pouring over its top and running down
			var gilt := "M72 124 L128 124 L128 150 Q124 158 120 150 L120 176 Q116 184 112 176 L112 158 Q104 168 96 158 L96 188 Q92 196 88 188 L88 156 Q80 164 72 152 Z"
			return _backdrop() \
				+ _ring(100, 84, 16, GOLD, 2.5) + _circle(100, 84, 4, GOLD, 0, GOLD) + _rays(100, 84, 22, 30, 12, GOLD, 1.4) \
				+ '<rect x="70" y="122" width="60" height="82" rx="5" fill="%s" stroke="%s" stroke-width="2.4"/>' % [INK, IVORY] \
				+ _fill(gilt, GOLD) + _circle(116, 196, 3, GOLD, 0, GOLD) + _circle(80, 170, 2.5, GOLD, 0, GOLD)
		"petrify":  # a block of stone split by a crack under a gaze: turn a card to Stone
			return _backdrop() \
				+ _path("M60 120 L100 98 L140 120 L140 184 L100 206 L60 184 Z", IVORY, 2.5) \
				+ _path("M60 120 L100 142 L140 120 M100 142 L100 206", GOLD, 1.4) \
				+ _path("M118 132 L110 150 L120 162 L112 182", PARCH, 1.6) + _path("M74 150 L82 162 L76 174", PARCH, 1.4) \
				+ _path("M76 72 Q100 56 124 72 Q100 88 76 72 Z", GOLD, 2) + _circle(100, 72, 4, GOLD, 0, GOLD) \
				+ _line(90, 84, 84, 96, GOLD, 1, 'stroke-dasharray="2 3"') + _line(110, 84, 116, 96, GOLD, 1, 'stroke-dasharray="2 3"')
		"kindle":  # a radiant diamond: turn cards into Diamonds
			return _rays(100, 142, 50, 70, 16, GOLD, 1.2) \
				+ _suit("diamond", 100, 142, 44) + _path("M100 98 L100 186 M70 142 L130 142", INK, 1.2, 'opacity="0.5"') \
				+ _star(152, 86, 5, 2, IVORY) + _star(48, 196, 4, 1.6, IVORY) + _star(156, 196, 3, 1.2, GOLD)
		"bramble":  # a club wreathed in a thorned vine: turn cards into Clubs
			var thorns := ""
			for k in 12:
				var ang := deg_to_rad(k * 30 + 10)
				var r1 := 60.0
				thorns += _path("M%s %s L%s %s" % [100 + cos(ang) * r1, 142 + sin(ang) * r1, 100 + cos(ang + 0.1) * (r1 + 8), 142 + sin(ang + 0.1) * (r1 + 8)], GOLD, 1.6)
			return _path("M100 82 C 150 82 166 130 152 166 C 140 196 110 206 88 200 C 56 192 36 160 46 122 C 54 96 74 84 100 82", GOLD, 2) \
				+ thorns + _suit("club", 100, 140, 42) \
				+ _fill("M138 74 A12 12 0 1 0 150 90 A9 9 0 1 1 138 74 Z", IVORY)
		"bloom":  # a heart opening like a flower under rays: turn cards into Hearts
			var petals := ""
			for k in 8:
				petals += '<g transform="rotate(%d 100 142)">%s</g>' % [k * 45, _path("M100 98 C 92 82 100 70 100 70 C 100 70 108 82 100 98 Z", GOLD, 1.4)]
			return _rays(100, 142, 62, 74, 24, GOLD, 1) + petals + _suit("heart", 100, 146, 34) + _circle(100, 142, 3, INK, 0, INK)
		"conjure":  # a star drawn in a circle with a new charm's mask at its heart: create a charm
			var pts := []
			for k in 5:
				var ang := deg_to_rad(-90 + k * 144)
				pts.append("%s %s" % [100 + cos(ang) * 58, 142 + sin(ang) * 58])
			return _ring(100, 142, 62, GOLD, 2) + _ring(100, 142, 68, GOLD, 0.7) \
				+ _path("M" + " L".join(pts) + " Z", IVORY, 1.6) \
				+ _path("M78 130 Q100 116 122 130 L118 156 Q100 170 82 156 Z", IVORY, 2.5, "", INK) \
				+ _path("M78 130 L70 112 L88 124 M122 130 L130 112 L112 124 M100 118 L100 104", GOLD, 2) \
				+ _circle(70, 110, 3, GOLD, 0, GOLD) + _circle(130, 110, 3, GOLD, 0, GOLD) + _circle(100, 102, 3, GOLD, 0, GOLD) \
				+ _circle(92, 140, 2, GOLD, 0, GOLD) + _circle(108, 140, 2, GOLD, 0, GOLD) + _path("M92 150 Q100 156 108 150", GOLD, 1.5)
		"shade":  # a spade in eclipse within a laurel ring: turn cards into Spades
			var laurel := ""
			for k in 9:
				var ang := deg_to_rad(110 + k * 18)
				var lx := 100 + cos(ang) * 64
				var ly := 142 + sin(ang) * 64
				laurel += _ellipse(lx, ly, 6, 2.5, GOLD, 1.2, 'transform="rotate(%d %s %s)"' % [rad_to_deg(ang) + 60, lx, ly])
				var rx := 200 - lx
				laurel += _ellipse(rx, ly, 6, 2.5, GOLD, 1.2, 'transform="rotate(%d %s %s)"' % [120 - rad_to_deg(ang), rx, ly])
			# an eclipse: a gold ring with a thin parchment crescent of light on one edge
			return laurel + _circle(100, 142, 46, GOLD, 1.5) \
				+ _fill("M118 100 A46 46 0 0 1 118 184 A52 52 0 0 0 118 100 Z", PARCH) \
				+ _suit("spade", 100, 142, 38)
	return ""


# ---------------------------------------------------------------- SVG pieces

static func _backdrop() -> String:
	return _ring(100, 142, 70, GOLD, 0.6, 'opacity="0.5"') \
		+ _ring(100, 142, 64, GOLD, 0.6, 'stroke-dasharray="1 5" opacity="0.8"') \
		+ _circle(100, 72, 2, GOLD, 0, GOLD) + _circle(170, 142, 2, GOLD, 0, GOLD) \
		+ _circle(100, 212, 2, GOLD, 0, GOLD) + _circle(30, 142, 2, GOLD, 0, GOLD)


static func _circle(x: float, y: float, r: float, stroke: String, w: float, extra := "", fill := "none") -> String:
	return '<circle cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" stroke-width="%s" %s/>' % [x, y, r, fill, stroke, w, extra]


static func _ring(x: float, y: float, r: float, stroke: String, w: float, extra := "") -> String:
	return _circle(x, y, r, stroke, w, extra)


static func _ellipse(x: float, y: float, rx: float, ry: float, stroke: String, w: float, extra := "") -> String:
	return '<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="none" stroke="%s" stroke-width="%s" %s/>' % [x, y, rx, ry, stroke, w, extra]


static func _line(x1: float, y1: float, x2: float, y2: float, stroke: String, w: float, extra := "") -> String:
	return '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s" stroke-linecap="round" %s/>' % [x1, y1, x2, y2, stroke, w, extra]


static func _path(d: String, stroke: String, w: float, extra := "", fill := "none") -> String:
	return '<path d="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linecap="round" stroke-linejoin="round" %s/>' % [d, fill, stroke, w, extra]


static func _fill(d: String, fill: String, opacity := 1.0) -> String:
	return '<path d="%s" fill="%s" opacity="%s"/>' % [d, fill, opacity]


static func _arc(x: float, y: float, r: float, from_deg: float, to_deg: float, stroke: String, w: float, extra := "") -> String:
	var a0 := deg_to_rad(from_deg)
	var a1 := deg_to_rad(to_deg)
	var large := 1 if absf(to_deg - from_deg) > 180 else 0
	return _path("M%s %s A%s %s 0 %d 1 %s %s" % [x + cos(a0) * r, y + sin(a0) * r, r, r, large, x + cos(a1) * r, y + sin(a1) * r], stroke, w, extra)


static func _rays(x: float, y: float, r0: float, r1: float, n: int, stroke: String, w: float) -> String:
	var out := ""
	for k in n:
		var ang := TAU * k / n
		out += _line(x + cos(ang) * r0, y + sin(ang) * r0, x + cos(ang) * r1, y + sin(ang) * r1, stroke, w)
	return out


## A four-pointed sparkle.
static func _star(x: float, y: float, r: float, inner: float, fill: String) -> String:
	var pts := []
	for k in 8:
		var ang := deg_to_rad(-90 + k * 45)
		var rr := r if k % 2 == 0 else inner
		pts.append("%s %s" % [x + cos(ang) * rr, y + sin(ang) * rr])
	return _fill("M" + " L".join(pts) + " Z", fill)


static func _hex(x: float, y: float, r: float, stroke: String) -> String:
	var pts := []
	for k in 6:
		var ang := deg_to_rad(-90 + k * 60)
		pts.append("%s %s" % [x + cos(ang) * r, y + sin(ang) * r])
	return _path("M" + " L".join(pts) + " Z", stroke, 2)


static func _plus(x: float, y: float, stroke: String) -> String:
	return _line(x - 6, y, x + 6, y, stroke, 2) + _line(x, y - 6, x, y + 6, stroke, 2)


## A small playing card outline, its top-left at (x, y), turned by `deg`.
static func _card(x: float, y: float, deg: float, stroke: String, opacity := 1.0) -> String:
	return '<g transform="rotate(%s %s %s)" opacity="%s">%s%s</g>' % [deg, x + 20, y + 28, opacity,
		'<rect x="%s" y="%s" width="40" height="56" rx="4" fill="%s" stroke="%s" stroke-width="2.2"/>' % [x, y, INK, stroke],
		'<rect x="%s" y="%s" width="32" height="48" rx="2" fill="none" stroke="%s" stroke-width="0.7" opacity="0.7"/>' % [x + 4, y + 4, GOLD]]


## A suit sign of half-height `s` centred on (x, y), in ivory with a gold edge.
static func _suit(suit: String, x: float, y: float, s: float) -> String:
	var d := ""
	match suit:
		"heart":
			d = "M%s %s C %s %s %s %s %s %s C %s %s %s %s %s %s Z" % [
				x, y + s, x - s * 1.6, y - s * 0.1, x - s * 0.8, y - s * 1.3, x, y - s * 0.45,
				x + s * 0.8, y - s * 1.3, x + s * 1.6, y - s * 0.1, x, y + s]
		"diamond":
			d = "M%s %s L%s %s L%s %s L%s %s Z" % [x, y - s, x + s * 0.72, y, x, y + s, x - s * 0.72, y]
		"spade":
			d = "M%s %s C %s %s %s %s %s %s C %s %s %s %s %s %s Z M%s %s L%s %s L%s %s Z" % [
				x, y - s, x + s * 1.5, y + s * 0.05, x + s * 0.7, y + s * 0.95, x, y + s * 0.35,
				x - s * 0.7, y + s * 0.95, x - s * 1.5, y + s * 0.05, x, y - s,
				x, y + s * 0.2, x + s * 0.35, y + s, x - s * 0.35, y + s]
		"club":
			var r := s * 0.42
			return _circle(x, y - s * 0.45, r, GOLD, 1.5, "", IVORY) + _circle(x - s * 0.48, y + s * 0.15, r, GOLD, 1.5, "", IVORY) \
				+ _circle(x + s * 0.48, y + s * 0.15, r, GOLD, 1.5, "", IVORY) \
				+ _path("M%s %s L%s %s L%s %s Z" % [x, y, x + s * 0.32, y + s, x - s * 0.32, y + s], GOLD, 1.5, "", IVORY)
	return _path(d, GOLD, 1.5, "", IVORY)
