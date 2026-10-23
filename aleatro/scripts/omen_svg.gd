class_name OmenSVG
extends RefCounted

## Omen cards as SVG in a minimal mystical style, rasterised at the size
## shown. Kept in separate parts:
##   frame()   - shared card: slate field, thin double border, corner
##               marks, faint atmosphere, bottom nameplate with side dots
##   emblem()  - each Omen's sign, in the 200 x 300 card space
## SpellView writes the Omen's name on the nameplate in the game font.

const VIEW_W := 200.0
const VIEW_H := 300.0
const NAME := Rect2(30, 254, 140, 26)   # nameplate, in card units

const NAVY := "#1a2236"
const SLATE := "#2e3d5c"
const BLUE := "#5b6f95"
const IVORY := "#f1ead8"
const GOLD := "#c9a24a"

static var _cache := {}


static func has_art(id: String) -> bool:
	return emblem(id) != ""


static func texture(id: String, px_w: int) -> ImageTexture:
	var key := "%s@%d" % [id, px_w]
	if not _cache.has(key):
		var img := Image.new()
		img.load_svg_from_string(svg(id), px_w / VIEW_W)
		_cache[key] = ImageTexture.create_from_image(img)
	return _cache[key]


## Emblems drawn a little small are enlarged about the card's centre.
const GROW := {"courtiers": 1.25, "reaper": 1.15, "chant": 1.3, "sigil": 1.1}


static func svg(id: String) -> String:
	var art := emblem(id)
	if GROW.has(id):
		art = '<g transform="translate(100 132) scale(%s) translate(-100 -132)">%s</g>' % [GROW[id], art]
	return '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="300" viewBox="0 0 200 300">%s%s</svg>' \
		% [frame(), art]


## The shared card, everything but the emblem and the name text.
static func frame() -> String:
	var out := [
		'<rect x="0" y="0" width="200" height="300" rx="12" fill="%s"/>' % NAVY,
		'<rect x="5" y="5" width="190" height="290" rx="9" fill="%s"/>' % SLATE,
		# atmosphere: two faint drifting arcs of mist
		'<path d="M14 92 Q70 70 120 96 T190 90" fill="none" stroke="%s" stroke-width="10" opacity="0.18" stroke-linecap="round"/>' % BLUE,
		'<path d="M10 206 Q64 222 116 200 T192 210" fill="none" stroke="%s" stroke-width="8" opacity="0.14" stroke-linecap="round"/>' % BLUE,
		# thin double border
		'<rect x="11" y="11" width="178" height="278" rx="6" fill="none" stroke="%s" stroke-width="1.2"/>' % BLUE,
		'<rect x="15" y="15" width="170" height="270" rx="4" fill="none" stroke="%s" stroke-width="0.6" opacity="0.7"/>' % BLUE,
		# nameplate with a dot at each end
		'<rect x="%s" y="%s" width="%s" height="%s" rx="4" fill="%s" stroke="%s" stroke-width="1"/>' \
			% [NAME.position.x, NAME.position.y, NAME.size.x, NAME.size.y, NAVY, BLUE],
		'<circle cx="%s" cy="%s" r="2.2" fill="%s"/>' % [NAME.position.x + 9, NAME.position.y + NAME.size.y / 2, GOLD],
		'<circle cx="%s" cy="%s" r="2.2" fill="%s"/>' % [NAME.end.x - 9, NAME.position.y + NAME.size.y / 2, GOLD],
	]
	# corner marks: a small diamond in each inner corner
	for c in [[22, 22], [178, 22], [22, 244], [178, 244]]:
		out.append('<path d="M%d %d l4 4 l-4 4 l-4 -4 Z" fill="none" stroke="%s" stroke-width="0.9"/>' % [c[0], c[1] - 4, GOLD])
	return "".join(out)


# ---------------------------------------------------------------- emblems
# Each sign sits about (100, 132) within r = 70: ivory for the figure at
# 2.8 wide, pale blue for secondary shapes at 1.4, gold only for accents.

static func emblem(id: String) -> String:
	var I := IVORY
	var B := BLUE
	var G := GOLD
	match id:
		"courtiers":  # a familiar, a cat, beneath three floating crowns: face cards arrive
			return _path("M74 196 Q70 150 86 130 L80 106 L94 120 Q100 117 106 120 L120 106 L114 130 Q130 150 126 196 Z", I, 2.8, NAVY) \
				+ _path("M126 190 Q150 192 146 168", I, 2.8) + _dot(92, 140, 2.2, G) + _dot(108, 140, 2.2, G) \
				+ _crown(70, 76, G) + _crown(100, 64, G) + _crown(130, 76, G)
		"reaper":  # a scythe cutting down through a card, two aces rising
			return _card(70, 132, -14, B) + _path("M64 140 L106 196", I, 1.4, "none", 'stroke-dasharray="3 3"') \
				+ _path("M128 70 L96 214", I, 2.8) + _path("M128 70 Q78 60 52 96 Q86 80 122 92", I, 2.8, NAVY) \
				+ _ace(140, 150, G) + _ace(150, 186, G)
		"chant":  # four numbered stones circling a mouth of sound: a chant
			var out := _arcs(100, 136, [16, 26, 36], B)
			for k in 4:
				var a := deg_to_rad(-140 + k * 33)
				var x := 100 + cos(a) * 62
				var y := 150 + sin(a) * 62
				out += '<rect x="%s" y="%s" width="18" height="18" rx="3" fill="%s" stroke="%s" stroke-width="2.4" transform="rotate(%d %s %s)"/>' % [x - 9, y - 9, NAVY, I, k * 12 - 18, x, y]
				out += _dot(x, y, 2.4, G)
			return out + _path("M86 150 Q100 166 114 150", I, 2.8) + _dot(100, 136, 3, I)
		"talisman":  # a radiant medallion: a Golden Seal
			return _rays(100, 132, 38, 62, 16, B, 1.4) + _ring(100, 132, 34, I, 2.8, NAVY) + _ring(100, 132, 26, G, 1.4) \
				+ _star(100, 132, 14, 5, G) + _dot(100, 132, 3, NAVY)
		"aura":  # a card wrapped in widening rings: an edition
			return _ring(100, 132, 66, B, 1.4, "none", 'opacity="0.6"') + _ring(100, 132, 54, B, 1.4) + _ring(100, 132, 42, I, 2.8) \
				+ _card(84, 110, 0, I) + _arc(100, 132, 54, -60, 10, G, 2.4)
		"wraith":  # a hooded spectre trailing away, one coin slipping from it: money to $0
			return _path("M100 66 Q132 68 136 112 Q140 156 152 196 Q138 188 128 200 Q118 186 106 202 Q96 186 84 200 Q74 188 60 196 Q66 156 64 112 Q68 68 100 66 Z", I, 2.8, NAVY) \
				+ _path("M82 104 Q100 90 118 104 L114 124 Q100 132 86 124 Z", B, 1.4, B) + _dot(92, 112, 2.2, I) + _dot(108, 112, 2.2, I) \
				+ _ring(146, 84, 8, G, 2) + _path("M146 96 L146 104 M140 110 L134 116", G, 1.4)
		"converge":  # four suits drawn inward to a single point: one suit
			return _line(52, 84, 92, 124, B, 1.4) + _line(148, 84, 108, 124, B, 1.4) + _line(52, 180, 92, 140, B, 1.4) + _line(148, 180, 108, 140, B, 1.4) \
				+ _suit("spade", 46, 78, 9) + _suit("heart", 154, 78, 9) + _suit("club", 46, 186, 9) + _suit("diamond", 154, 186, 9) \
				+ _ring(100, 132, 16, I, 2.8, NAVY) + _dot(100, 132, 4, G)
		"mono":  # a talking board: every letter circling one rank
			var out := _arc(100, 150, 64, 200, 340, B, 1.4)
			for k in 9:
				var a := deg_to_rad(200 + k * 17.5)
				out += _dot(100 + cos(a) * 64, 150 + sin(a) * 64, 2.6, I)
			return out + _path("M100 104 L128 158 L100 182 L72 158 Z", I, 2.8, NAVY) + _ring(100, 152, 9, G, 2) \
				+ _line(100, 182, 100, 206, B, 1.4) + _line(84, 206, 116, 206, B, 1.4)
		"void":  # negative space: a dark hole ringed in light, one drip falling
			return _ring(100, 128, 50, I, 2.8, NAVY) + _ring(100, 128, 60, B, 1.4, "none", 'stroke-dasharray="2 6"') \
				+ _ring(100, 128, 30, B, 1.4) + _path("M100 178 Q108 192 100 204 Q92 192 100 178 Z", I, 2, I) + _dot(100, 128, 3, G)
		"pyre":  # a tall flame over a heap of five cards: burn them for gold
			var out := ""
			for k in 5:
				out += _card(56 + k * 18, 170, (k - 2) * 9, B)
			return out + _path("M100 62 C 124 94 142 116 132 150 C 126 170 112 178 100 178 C 84 178 68 166 68 146 C 68 122 86 112 88 92 C 96 106 96 118 100 124 C 108 104 104 82 100 62 Z", I, 2.8, NAVY) \
				+ _path("M100 120 C 110 136 114 150 106 162 C 102 168 96 168 92 160 C 88 150 94 140 100 120 Z", G, 1.4, G)
		"rebirth":  # an ankh: one life carried over, the rest let go
			return _ring(100, 132, 62, B, 1.4) + _ellipse(100, 92, 20, 26, I, 2.8) \
				+ _line(100, 118, 100, 200, I, 6) + _line(68, 128, 132, 128, I, 6) + _dot(100, 92, 3, G)
		"sigil":  # a seal stamped twice, the second an echo: retrigger
			return _seal(88, 124, I, NAVY) + '<g opacity="0.45">' + _seal(116, 148, B, "none") + '</g>' \
				+ _path("M136 178 Q150 192 140 206", G, 2)
		"curse":  # a fractured circle, one shard lit: one charm kept, the rest broken
			return _arc(100, 132, 52, 20, 140, I, 2.8) + _arc(100, 132, 52, 160, 250, I, 2.8) + _arc(100, 132, 52, 270, 350, G, 2.8) \
				+ _path("M100 72 L92 108 L108 124 L94 156 L104 192", B, 1.4) + _path("M150 108 L132 120 M50 150 L68 140", B, 1.4) \
				+ _star(100, 132, 10, 3.5, G)
		"lull":  # a slow spiral pulling inward: an Azure Seal
			var pts := []
			var t := 0.0
			while t < 5.2 * PI:
				var r := 4 + t * 3.6
				pts.append("%s %s" % [100 + cos(t) * r, 132 + sin(t) * r])
				t += 0.18
			return _path("M" + " L".join(pts), I, 2.8) + _dot(100, 132, 3, G) + _ring(100, 132, 66, B, 1.4, "none", 'stroke-dasharray="2 5"')
		"whisper":  # a candle whose smoke curls into a whisper: a Violet Seal
			return '<rect x="84" y="140" width="32" height="66" rx="3" fill="%s" stroke="%s" stroke-width="2.8"/>' % [NAVY, I] \
				+ _line(70, 206, 130, 206, B, 1.4) + _path("M100 140 L100 130", I, 2) \
				+ _path("M100 128 C 108 118 108 110 100 100 C 92 110 92 118 100 128 Z", G, 1.4, G) \
				+ _path("M100 96 Q86 84 98 72 Q110 60 96 48", B, 1.4) + _path("M110 90 Q126 82 120 66", B, 1.4)
		"duplicate":  # an antlered creature and its double: two copies of a card
			return '<g opacity="0.45" transform="translate(14 10)">' + _beast(B) + '</g>' + _beast(I)
		"soul":  # a winged flame rising: a Legendary charm
			return _path("M100 72 C 116 96 124 112 118 134 C 114 148 106 154 100 154 C 92 154 82 146 82 132 C 82 114 96 104 100 72 Z", I, 2.8, NAVY) \
				+ _path("M82 136 Q52 120 40 96 Q64 104 84 120", I, 2.4) + _path("M118 136 Q148 120 160 96 Q136 104 116 120", I, 2.4) \
				+ _dot(100, 128, 4, G) + _line(100, 158, 100, 204, B, 1.4) + _star(100, 214, 7, 2.5, G)
		"singularity":  # a black hole: a dark core inside a tilted ring, everything drawn in
			var out := ""
			for k in 8:
				var a := deg_to_rad(k * 45 + 22)
				out += _line(100 + cos(a) * 66, 132 + sin(a) * 66, 100 + cos(a) * 44, 132 + sin(a) * 44, B, 1.4)
			return out + '<ellipse cx="100" cy="132" rx="62" ry="16" transform="rotate(-20 100 132)" fill="none" stroke="%s" stroke-width="2.4"/>' % G \
				+ _ring(100, 132, 26, I, 2.8, NAVY) + _dot(100, 132, 3, I)
	return ""


# ---------------------------------------------------------------- SVG pieces

static func _ring(x: float, y: float, r: float, stroke: String, w: float, fill := "none", extra := "") -> String:
	return '<circle cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" stroke-width="%s" %s/>' % [x, y, r, fill, stroke, w, extra]


static func _ellipse(x: float, y: float, rx: float, ry: float, stroke: String, w: float) -> String:
	return '<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="none" stroke="%s" stroke-width="%s"/>' % [x, y, rx, ry, stroke, w]


static func _dot(x: float, y: float, r: float, fill: String) -> String:
	return '<circle cx="%s" cy="%s" r="%s" fill="%s"/>' % [x, y, r, fill]


static func _line(x1: float, y1: float, x2: float, y2: float, stroke: String, w: float) -> String:
	return '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s" stroke-linecap="round"/>' % [x1, y1, x2, y2, stroke, w]


static func _path(d: String, stroke: String, w: float, fill := "none", extra := "") -> String:
	return '<path d="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linecap="round" stroke-linejoin="round" %s/>' % [d, fill, stroke, w, extra]


static func _arc(x: float, y: float, r: float, from_deg: float, to_deg: float, stroke: String, w: float) -> String:
	var a0 := deg_to_rad(from_deg)
	var a1 := deg_to_rad(to_deg)
	var large := 1 if absf(to_deg - from_deg) > 180 else 0
	return _path("M%s %s A%s %s 0 %d 1 %s %s" % [x + cos(a0) * r, y + sin(a0) * r, r, r, large, x + cos(a1) * r, y + sin(a1) * r], stroke, w)


static func _arcs(x: float, y: float, radii: Array, stroke: String) -> String:
	var out := ""
	for r in radii:
		out += _arc(x, y, r, 200, 340, stroke, 1.4)
	return out


static func _rays(x: float, y: float, r0: float, r1: float, n: int, stroke: String, w: float) -> String:
	var out := ""
	for k in n:
		var a := TAU * k / n
		out += _line(x + cos(a) * r0, y + sin(a) * r0, x + cos(a) * r1, y + sin(a) * r1, stroke, w)
	return out


static func _star(x: float, y: float, r: float, inner: float, fill: String) -> String:
	var pts := []
	for k in 8:
		var a := deg_to_rad(-90 + k * 45)
		var rr := r if k % 2 == 0 else inner
		pts.append("%s %s" % [x + cos(a) * rr, y + sin(a) * rr])
	return '<path d="M%s Z" fill="%s"/>' % [" L".join(pts), fill]


static func _crown(x: float, y: float, stroke: String) -> String:
	return _path("M%s %s L%s %s L%s %s L%s %s L%s %s L%s %s L%s %s Z" % [
		x - 11, y + 6, x - 12, y - 6, x - 5, y, x, y - 9, x + 5, y, x + 12, y - 6, x + 11, y + 6], stroke, 2, NAVY)


## A small card outline, its top-left at (x, y), turned by `deg`.
static func _card(x: float, y: float, deg: float, stroke: String) -> String:
	return '<rect x="%s" y="%s" width="32" height="44" rx="3" fill="%s" stroke="%s" stroke-width="2" transform="rotate(%s %s %s)"/>' \
		% [x, y, NAVY, stroke, deg, x + 16, y + 22]


static func _ace(x: float, y: float, stroke: String) -> String:
	return _path("M%s %s L%s %s L%s %s M%s %s L%s %s" % [x - 7, y + 9, x, y - 9, x + 7, y + 9, x - 4, y + 2, x + 4, y + 2], stroke, 2.4)


## A round wax seal with a star pressed into it.
static func _seal(x: float, y: float, stroke: String, fill: String) -> String:
	var out := _ring(x, y, 30, stroke, 2.8, fill)
	for k in 8:
		var a := deg_to_rad(k * 45 + 22.5)
		out += _dot(x + cos(a) * 30, y + sin(a) * 30, 3.5, stroke)
	return out + _ring(x, y, 20, stroke, 1.4) + _star(x, y, 12, 4, stroke)


## An antlered head seen from the front.
static func _beast(stroke: String) -> String:
	return _path("M92 112 Q100 104 108 112 L114 150 Q108 176 100 182 Q92 176 86 150 Z", stroke, 2.6, NAVY) \
		+ _path("M92 112 Q80 96 76 72 M80 90 L64 84 M78 78 L70 62 M108 112 Q120 96 124 72 M120 90 L136 84 M122 78 L130 62", stroke, 2.4) \
		+ _dot(94, 136, 2.2, GOLD) + _dot(106, 136, 2.2, GOLD)


## A suit sign of half-height s, outlined in ivory.
static func _suit(suit: String, x: float, y: float, s: float) -> String:
	var d := ""
	match suit:
		"heart":
			d = "M%s %s C %s %s %s %s %s %s C %s %s %s %s %s %s Z" % [x, y + s, x - s * 1.6, y - s * 0.1, x - s * 0.8, y - s * 1.3, x, y - s * 0.45,
				x + s * 0.8, y - s * 1.3, x + s * 1.6, y - s * 0.1, x, y + s]
		"diamond":
			d = "M%s %s L%s %s L%s %s L%s %s Z" % [x, y - s, x + s * 0.72, y, x, y + s, x - s * 0.72, y]
		"spade":
			d = "M%s %s C %s %s %s %s %s %s C %s %s %s %s %s %s Z M%s %s L%s %s L%s %s Z" % [
				x, y - s, x + s * 1.5, y + s * 0.05, x + s * 0.7, y + s * 0.95, x, y + s * 0.35,
				x - s * 0.7, y + s * 0.95, x - s * 1.5, y + s * 0.05, x, y - s, x, y + s * 0.2, x + s * 0.35, y + s, x - s * 0.35, y + s]
		"club":
			var r := s * 0.42
			return _ring(x, y - s * 0.45, r, IVORY, 1.6, NAVY) + _ring(x - s * 0.48, y + s * 0.15, r, IVORY, 1.6, NAVY) \
				+ _ring(x + s * 0.48, y + s * 0.15, r, IVORY, 1.6, NAVY) \
				+ _path("M%s %s L%s %s L%s %s Z" % [x, y, x + s * 0.32, y + s, x - s * 0.32, y + s], IVORY, 1.6, NAVY)
	return _path(d, IVORY, 1.6, NAVY)
