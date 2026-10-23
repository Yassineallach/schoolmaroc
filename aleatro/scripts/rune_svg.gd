class_name RuneSVG
extends RefCounted

## Rune cards as SVG, in a minimal celestial style, rasterised at the size
## shown so lines stay sharp. Kept in separate parts:
##   frame()     - shared card: teal field, thin double border, corners,
##                 title plate, a few stars, bottom section
##   emblem()    - each hand's geometric sign, in the 200 x 300 card space
##   card_row()  - the bottom indicators: how many cards make the hand
## SpellView writes the hand's name on the title plate in the game font.

const VIEW_W := 200.0
const VIEW_H := 300.0
const TITLE := Rect2(36, 22, 128, 24)   # title plate, in card units

const NAVY := "#16263a"
const TEAL := "#2f5762"
const IVORY := "#f1ead8"
const CYAN := "#a9d6dc"
const SILVER := "#b8c2c8"

## Cards that make each hand, shown as small card outlines along the bottom.
const CARDS := {
	"High Card": 1, "Pair": 2, "Two Pair": 4, "Three of a Kind": 3, "Straight": 5, "Flush": 5,
	"Full House": 5, "Four of a Kind": 4, "Straight Flush": 5, "Five of a Kind": 5,
	"Flush House": 5, "Flush Five": 5,
}

static var _cache := {}


static func texture(hand: String, px_w: int) -> ImageTexture:
	var key := "%s@%d" % [hand, px_w]
	if not _cache.has(key):
		var img := Image.new()
		img.load_svg_from_string(svg(hand), px_w / VIEW_W)
		_cache[key] = ImageTexture.create_from_image(img)
	return _cache[key]


static func svg(hand: String) -> String:
	return '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="300" viewBox="0 0 200 300">%s%s%s</svg>' \
		% [frame(), emblem(hand), card_row(CARDS.get(hand, 1))]


## The shared card, without the emblem, indicators or title text.
static func frame() -> String:
	var out := [
		'<rect x="0" y="0" width="200" height="300" rx="12" fill="%s"/>' % NAVY,
		'<rect x="5" y="5" width="190" height="290" rx="9" fill="%s"/>' % TEAL,
		# thin double border
		'<rect x="11" y="11" width="178" height="278" rx="6" fill="none" stroke="%s" stroke-width="1.2"/>' % CYAN,
		'<rect x="15" y="15" width="170" height="270" rx="4" fill="none" stroke="%s" stroke-width="0.6" opacity="0.6"/>' % CYAN,
		# title plate
		'<rect x="%s" y="%s" width="%s" height="%s" rx="12" fill="%s" stroke="%s" stroke-width="1"/>' \
			% [TITLE.position.x, TITLE.position.y, TITLE.size.x, TITLE.size.y, NAVY, IVORY],
		# bottom section: divider and a quiet band for the indicators
		'<line x1="30" y1="238" x2="170" y2="238" stroke="%s" stroke-width="0.7" opacity="0.8"/>' % CYAN,
		'<circle cx="100" cy="238" r="2.2" fill="%s"/>' % IVORY,
		'<line x1="30" y1="270" x2="170" y2="270" stroke="%s" stroke-width="0.5" opacity="0.5"/>' % CYAN,
	]
	# corners: a quarter arc and a dot tucked into each inner corner
	for c in [[22, 22, 0], [178, 22, 90], [178, 278, 180], [22, 278, 270]]:
		out.append('<g transform="rotate(%d %d %d)"><path d="M%d %d A8 8 0 0 1 %d %d" fill="none" stroke="%s" stroke-width="0.9"/><circle cx="%d" cy="%d" r="1.2" fill="%s"/></g>' \
			% [c[2], c[0], c[1], c[0], c[1] + 8, c[0] + 8, c[1], CYAN, c[0] + 3, c[1] + 3, IVORY])
	# a few fixed stars and dots across the field
	for st in [[34, 66, 3.2], [168, 74, 2.4], [30, 196, 2.4], [170, 210, 3.2], [150, 58, 1.6], [52, 222, 1.6]]:
		out.append(_twinkle(st[0], st[1], st[2], SILVER))
	for d in [[60, 62], [140, 220], [176, 140], [24, 132], [118, 60], [80, 226]]:
		out.append('<circle cx="%d" cy="%d" r="0.9" fill="%s" opacity="0.8"/>' % [d[0], d[1], CYAN])
	return "".join(out)


## n small card outlines centred in the bottom band.
static func card_row(n: int) -> String:
	var w := 9.0
	var gap := 6.0
	var x := 100.0 - (n * w + (n - 1) * gap) / 2.0
	var out := ""
	for k in n:
		out += '<rect x="%s" y="247" width="%s" height="13" rx="1.5" fill="none" stroke="%s" stroke-width="1.1"/>' % [x, w, IVORY]
		out += '<circle cx="%s" cy="253.5" r="1" fill="%s"/>' % [x + w / 2.0, CYAN]
		x += w + gap
	return out


# ---------------------------------------------------------------- emblems
# Each sign is drawn about (100, 140) within r = 62: ivory for the main
# figure at 2.6 wide, pale cyan for the construction lines at 1.2.

static func emblem(hand: String) -> String:
	var I := IVORY
	var Cy := CYAN
	match hand:
		"High Card":  # a lone star above a single upright stroke: one card stands alone
			return _guide(56) + _line(100, 108, 100, 196, I, 3.0) + _line(82, 196, 118, 196, I, 3.0) \
				+ _star(100, 92, 14, 4, I) + _ring(100, 92, 22, Cy, 1.2)
		"Pair":  # two overlapping circles and the lens they share
			return _guide(60) + _ring(82, 140, 30, I, 3.0) + _ring(118, 140, 30, I, 3.0) \
				+ _line(100, 116, 100, 164, Cy, 1.2) + _dot(100, 140, 3, I)
		"Two Pair":  # two linked pairs, one above the other
			return _guide(60) + _ring(84, 116, 16, I, 3.0) + _ring(116, 116, 16, I, 3.0) \
				+ _ring(84, 166, 16, I, 3.0) + _ring(116, 166, 16, I, 3.0) \
				+ _line(100, 96, 100, 186, Cy, 1.2) + _line(68, 141, 132, 141, Cy, 1.2)
		"Three of a Kind":  # a triangle with a circle at each corner
			var p := _tri(100, 146, 46)
			return _guide(60) + _poly(p, I, 3.0) + _ring(p[0].x, p[0].y, 9, I, 3.0, NAVY) \
				+ _ring(p[1].x, p[1].y, 9, I, 3.0, NAVY) + _ring(p[2].x, p[2].y, 9, I, 3.0, NAVY) + _ring(100, 146, 14, Cy, 1.2)
		"Straight":  # five stars climbing in a line toward an arrowhead
			var out := _guide(60) + _line(62, 182, 140, 100, Cy, 1.2) + _path("M126 100 L140 100 L140 114", I, 3.0)
			for k in 5:
				out += _dot(62 + k * 17, 182 - k * 18, 6 if k == 4 else 4.5, I)
			return out
		"Flush":  # one crescent carrying five beads: all of a single kind
			var out := _guide(60) + _path("M112 96 A46 46 0 1 0 112 184 A38 38 0 1 1 112 96 Z", I, 3.0)
			for k in 5:
				var a := deg_to_rad(130 + k * 25)
				out += _dot(100 + cos(a) * 56, 140 + sin(a) * 56, 3.2, Cy)
			return out
		"Full House":  # a triangle of three over a square of two
			return _guide(60) + _poly(_tri(100, 112, 30), I, 3.0) + _path("M70 132 L130 132 L130 188 L70 188 Z", I, 3.0) \
				+ _dot(100, 100, 3, Cy) + _dot(90, 118, 3, Cy) + _dot(110, 118, 3, Cy) \
				+ _dot(88, 160, 3.5, I) + _dot(112, 160, 3.5, I)
		"Four of a Kind":  # a square standing on its point, four circles at its corners
			return _guide(60) + _path("M100 92 L148 140 L100 188 L52 140 Z", I, 3.0) \
				+ _ring(100, 92, 7, I, 2.4, TEAL) + _ring(148, 140, 7, I, 2.4, TEAL) + _ring(100, 188, 7, I, 2.4, TEAL) + _ring(52, 140, 7, I, 2.4, TEAL) \
				+ _path("M100 116 L124 140 L100 164 L76 140 Z", Cy, 1.2)
		"Straight Flush":  # a comet: one bright head with a fan of straight tail lines
			var out := _guide(60) + _ring(122, 116, 13, I, 3.0) + _dot(122, 116, 4, I)
			for k in 5:
				var off := (k - 2) * 7.0
				out += _line(112 + off * 0.7, 126 + off * 0.7, 62 + off * 1.6, 176 + off * 1.6, Cy if k % 2 else I, 1.2 if k % 2 else 2)
			return out
		"Five of a Kind":  # a five-pointed star drawn in a circle
			var pts := []
			for k in 5:
				var a := deg_to_rad(-90 + k * 144)
				pts.append(Vector2(100 + cos(a) * 52, 140 + sin(a) * 52))
			return _ring(100, 140, 58, I, 3.0) + _poly(pts, I, 2.2) + _ring(100, 140, 20, Cy, 1.2)
		"Flush House":  # a ringed world: three beads on the ring, two upon the sphere
			return _guide(60) + _ring(100, 140, 30, I, 3.0) \
				+ '<ellipse cx="100" cy="140" rx="60" ry="15" transform="rotate(-18 100 140)" fill="none" stroke="%s" stroke-width="2"/>' % I \
				+ _dot(46, 160, 3.2, Cy) + _dot(154, 120, 3.2, Cy) + _dot(70, 168, 3.2, Cy) + _dot(92, 132, 3, I) + _dot(108, 148, 3, I)
		"Flush Five":  # an eclipse: a crescent over a sun of five rays
			var out := _guide(60) + _ring(100, 140, 26, I, 3.0)
			for k in 5:
				var a := deg_to_rad(-90 + k * 72)
				out += _line(100 + cos(a) * 34, 140 + sin(a) * 34, 100 + cos(a) * 54, 140 + sin(a) * 54, I, 3.0)
			return out + _crescent(108, 132, 20, 8, Cy) + _dot(100, 140, 3, I)
	return ""


# ---------------------------------------------------------------- SVG pieces

## A faint guide circle behind every sign, so all twelve share a rhythm.
static func _guide(r: float) -> String:
	return _ring(100, 140, r, CYAN, 0.6, "none", 'stroke-dasharray="1.5 5" opacity="0.7"')


static func _ring(x: float, y: float, r: float, stroke: String, w: float, fill := "none", extra := "") -> String:
	return '<circle cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" stroke-width="%s" %s/>' % [x, y, r, fill, stroke, w, extra]


static func _dot(x: float, y: float, r: float, fill: String) -> String:
	return '<circle cx="%s" cy="%s" r="%s" fill="%s"/>' % [x, y, r, fill]


static func _line(x1: float, y1: float, x2: float, y2: float, stroke: String, w: float) -> String:
	return '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s" stroke-linecap="round"/>' % [x1, y1, x2, y2, stroke, w]


static func _path(d: String, stroke: String, w: float) -> String:
	return '<path d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" stroke-linejoin="round"/>' % [d, stroke, w]


static func _poly(pts: Array, stroke: String, w: float) -> String:
	var parts := []
	for p in pts:
		parts.append("%s %s" % [p.x, p.y])
	return _path("M" + " L".join(parts) + " Z", stroke, w)


## Corners of an upward triangle of circumradius r.
static func _tri(x: float, y: float, r: float) -> Array:
	var out := []
	for k in 3:
		var a := deg_to_rad(-90 + k * 120)
		out.append(Vector2(x + cos(a) * r, y + sin(a) * r))
	return out


## A crescent opening to the right: outer circle r, bite offset `bite`.
static func _crescent(x: float, y: float, r: float, bite: float, fill: String) -> String:
	var tx := x + bite * 0.3
	var ri := r - bite * 0.5
	return '<path d="M%s %s A%s %s 0 1 0 %s %s A%s %s 0 0 1 %s %s Z" fill="%s"/>' % [
		tx, y - r * 0.96, r, r, tx, y + r * 0.96, ri, ri, tx, y - r * 0.96, fill]


## A four-pointed star.
static func _star(x: float, y: float, r: float, inner: float, fill: String) -> String:
	var pts := []
	for k in 8:
		var a := deg_to_rad(-90 + k * 45)
		var rr := r if k % 2 == 0 else inner
		pts.append("%s %s" % [x + cos(a) * rr, y + sin(a) * rr])
	return '<path d="M%s Z" fill="%s"/>' % [" L".join(pts), fill]


static func _twinkle(x: float, y: float, r: float, fill: String) -> String:
	return _star(x, y, r, r * 0.28, fill)
