class_name CharmSVG
extends RefCounted

## Charm cards as SVG: a shared frame in the charm's rarity colour, and an
## illustration built from a small vocabulary of drawing primitives. Each
## charm's entry in CharmIcons.ICONS names the object it depicts and holds
## its "art": a list of operations, so icons stay short, consistent in line
## weight and easy to edit.
##
## Icons are drawn in a 100 x 100 box placed in the middle of the 120 x 150
## card; rasterised at the size shown so edges stay sharp.

const VIEW_W := 120.0
const VIEW_H := 150.0
const ICON_AT := Vector2(10, 26)       # top-left of the 100 x 100 icon box
const STROKE := 2.6                    # outline width used everywhere

## The shared palette; recipes name colours by these keys.
const COL := {
	"K": "#2a2430", "gold": "#c9a24a", "bronze": "#9c6b3c", "ivory": "#f1ead8", "parch": "#e3d5b8",
	"blue": "#3b5b92", "navy": "#24365c", "slate": "#5b6577", "teal": "#3f8f8a", "green": "#4f8a4a",
	"red": "#b0453f", "purple": "#6c4a8f", "pink": "#d58a8a", "white": "#fbf7ec", "sky": "#8fb8d8",
	"brown": "#6b4a2e", "choc": "#4a3222", "mint": "#8fd1b0", "none": "none",
}
const RARITY := ["#4a6fa5", "#3f9a5a", "#b8334a", "#8f5bd6"]

static var _cache := {}


static func has_art(id: String) -> bool:
	return CharmIcons.ICONS.has(id)


static func texture(id: String, px_w: int) -> ImageTexture:
	var key := "%s@%d" % [id, px_w]
	if not _cache.has(key):
		var img := Image.new()
		img.load_svg_from_string(svg(id), px_w / VIEW_W)
		_cache[key] = ImageTexture.create_from_image(img)
	return _cache[key]


static func svg(id: String) -> String:
	var rarity: int = Data.charm_def(id).get("rarity", 0)
	return '<svg xmlns="http://www.w3.org/2000/svg" width="120" height="150" viewBox="0 0 120 150">%s<g transform="translate(%s %s)">%s</g></svg>' \
		% [frame(rarity), ICON_AT.x, ICON_AT.y, icon(id)]


## The card: ivory field, dark edge, a thin double border and a soft disc
## behind the icon in the rarity colour, plus rarity pips at the bottom.
static func frame(rarity: int) -> String:
	var rc: String = RARITY[clampi(rarity, 0, 3)]
	var out := '<rect x="0" y="0" width="120" height="150" rx="10" fill="%s"/>' % COL.K
	out += '<rect x="3" y="3" width="114" height="144" rx="8" fill="%s"/>' % COL.ivory
	out += '<rect x="7" y="7" width="106" height="136" rx="5" fill="none" stroke="%s" stroke-width="1.6"/>' % rc
	out += '<rect x="10" y="10" width="100" height="130" rx="3" fill="none" stroke="%s" stroke-width="0.7" opacity="0.7"/>' % rc
	out += '<circle cx="60" cy="76" r="46" fill="%s" opacity="0.55"/>' % COL.parch
	out += '<circle cx="60" cy="76" r="46" fill="none" stroke="%s" stroke-width="0.8" opacity="0.5"/>' % rc
	# rarity pips: one diamond per tier, centred under the icon
	var n := rarity + 1
	for k in n:
		var x := 60.0 + (k - (n - 1) / 2.0) * 9.0
		out += '<path d="M%s 128 l3.5 3.5 l-3.5 3.5 l-3.5 -3.5 Z" fill="%s"/>' % [x, rc]
	# a small notch at the top
	out += '<path d="M54 7 L66 7 L63 12 L57 12 Z" fill="%s"/>' % rc
	return out


static func icon(id: String) -> String:
	var out := ""
	for op in CharmIcons.ICONS[id].art if CharmIcons.ICONS.has(id) else []:
		out += draw(op)
	return out


# ---------------------------------------------------------------- operations
# Every operation is an array: [name, args...]. Colours are COL keys.

static func draw(op: Array) -> String:
	match op[0]:
		# --- basic shapes, outlined
		"c":  # circle x y r fill
			return _shape('<circle cx="%s" cy="%s" r="%s"' % [op[1], op[2], op[3]], op[4])
		"e":  # ellipse x y rx ry fill [rot]
			return _shape('<ellipse cx="%s" cy="%s" rx="%s" ry="%s"%s' % [op[1], op[2], op[3], op[4], _rot(op, 6, op[1], op[2])], op[5])
		"r":  # rect x y w h fill [rx] [rot]
			var rx: float = op[6] if op.size() > 6 else 2.0
			var rot := _rot(op, 7, op[1] + op[3] / 2.0, op[2] + op[4] / 2.0)
			return _shape('<rect x="%s" y="%s" width="%s" height="%s" rx="%s"%s' % [op[1], op[2], op[3], op[4], rx, rot], op[5])
		"p":  # path d fill
			return _shape('<path d="%s"' % op[1], op[2])
		"s":  # stroke-only path d colour width
			return '<path d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" stroke-linejoin="round"/>' % [op[1], COL[op[2]], op[3]]
		"l":  # line x1 y1 x2 y2 colour width
			return '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s" stroke-linecap="round"/>' % [op[1], op[2], op[3], op[4], COL[op[5]], op[6]]
		"dot":  # filled dot, no outline: x y r colour
			return '<circle cx="%s" cy="%s" r="%s" fill="%s"/>' % [op[1], op[2], op[3], COL[op[4]]]
		"box":  # flat rect, no outline: x y w h colour
			return '<rect x="%s" y="%s" width="%s" height="%s" fill="%s"/>' % [op[1], op[2], op[3], op[4], COL[op[5]]]
		"hi":  # small white highlight: x y r
			return '<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s" opacity="0.85" transform="rotate(-30 %s %s)"/>' % [op[1], op[2], op[3], op[3] * 0.55, COL.white, op[1], op[2]]
		"g":  # group: transform-string, ops...
			var inner := ""
			for k in range(2, op.size()):
				inner += draw(op[k])
			return '<g transform="%s">%s</g>' % [op[1], inner]
		# --- composite pieces
		"star":  # x y r points fill [inner]
			return _shape('<path d="%s"' % _star_d(op[1], op[2], op[3], op[4], op[6] if op.size() > 6 else 0.45), op[5])
		"spark":  # 4-point sparkle, no outline: x y r colour
			return '<path d="%s" fill="%s"/>' % [_star_d(op[1], op[2], op[3], 4, 0.25), COL[op[4]]]
		"suit":  # kind x y s fill
			return _shape('<path d="%s"' % _suit_d(op[1], op[2], op[3], op[4]), op[5])
		"coin":  # x y r [mark: "$", "star", ""]
			var x: float = op[1]
			var y: float = op[2]
			var r: float = op[3]
			var out := _shape('<circle cx="%s" cy="%s" r="%s"' % [x, y, r], "gold")
			out += '<circle cx="%s" cy="%s" r="%s" fill="none" stroke="%s" stroke-width="1.4"/>' % [x, y, r * 0.72, COL.bronze]
			var mark: String = op[4] if op.size() > 4 else "$"
			if mark == "$":
				out += draw(["s", "M%s %s Q%s %s %s %s Q%s %s %s %s Q%s %s %s %s" % [x + r * 0.3, y - r * 0.32, x, y - r * 0.5, x - r * 0.25, y - r * 0.2,
					x, y, x + r * 0.25, y + r * 0.2, x, y + r * 0.5, x - r * 0.3, y + r * 0.32], "bronze", 1.8])
				out += draw(["l", x, y - r * 0.55, x, y + r * 0.55, "bronze", 1.4])
			elif mark == "star":
				out += '<path d="%s" fill="%s"/>' % [_star_d(x, y, r * 0.42, 5, 0.45), COL.bronze]
			return out + draw(["hi", x - r * 0.45, y - r * 0.45, r * 0.22])
		"chip":  # poker chip: x y r fill
			var x: float = op[1]
			var y: float = op[2]
			var r: float = op[3]
			var out := _shape('<circle cx="%s" cy="%s" r="%s"' % [x, y, r], op[4])
			for k in 6:
				var a := TAU * k / 6.0
				out += '<rect x="%s" y="%s" width="%s" height="%s" fill="%s" transform="rotate(%s %s %s)"/>' % [
					x - r * 0.14, y - r, r * 0.28, r * 0.24, COL.white, rad_to_deg(a), x, y]
			return out + '<circle cx="%s" cy="%s" r="%s" fill="none" stroke="%s" stroke-width="1.4" stroke-dasharray="2 2"/>' % [x, y, r * 0.6, COL.white]
		"stack":  # a stack of chips seen side-on: x y(bottom) w count fill
			var x: float = op[1]
			var y: float = op[2]
			var w: float = op[3]
			var out := ""
			for k in op[4]:
				var yy: float = y - k * 7.0
				out += _shape('<ellipse cx="%s" cy="%s" rx="%s" ry="%s"' % [x, yy, w / 2.0, w * 0.2], op[5])
				out += '<path d="M%s %s h%s" stroke="%s" stroke-width="1.2" stroke-dasharray="3 3"/>' % [x - w * 0.42, yy + 1, w * 0.84, COL.white]
			return out
		"gem":  # cut gem: x y s fill
			var x: float = op[1]
			var y: float = op[2]
			var s: float = op[3]
			var out := _shape('<path d="M%s %s L%s %s L%s %s L%s %s L%s %s Z"' % [x - s, y - s * 0.3, x - s * 0.55, y - s * 0.8, x + s * 0.55, y - s * 0.8, x + s, y - s * 0.3, x, y + s], op[4])
			out += '<path d="M%s %s L%s %s M%s %s L%s %s L%s %s L%s %s" fill="none" stroke="%s" stroke-width="1.2" stroke-linejoin="round"/>' % [
				x - s, y - s * 0.3, x + s, y - s * 0.3, x - s * 0.55, y - s * 0.8, x - s * 0.25, y - s * 0.3, x, y + s, x + s * 0.25, y - s * 0.3, COL.K]
			return out + draw(["hi", x - s * 0.45, y - s * 0.5, s * 0.18])
		"ring":  # finger ring with a stone: x y s band stone
			var x: float = op[1]
			var y: float = op[2]
			var s: float = op[3]
			var out := '<circle cx="%s" cy="%s" r="%s" fill="none" stroke="%s" stroke-width="%s"/>' % [x, y + s * 0.35, s * 0.72, COL.K, s * 0.3 + 2 * STROKE]
			out += '<circle cx="%s" cy="%s" r="%s" fill="none" stroke="%s" stroke-width="%s"/>' % [x, y + s * 0.35, s * 0.72, COL[op[4]], s * 0.3]
			return out + draw(["gem", x, y - s * 0.55, s * 0.5, op[5]])
		"mask":  # theatre mask: x y s fill mood(smile|frown|blank)
			var x: float = op[1]
			var y: float = op[2]
			var s: float = op[3]
			var out := _shape('<path d="M%s %s Q%s %s %s %s Q%s %s %s %s Q%s %s %s %s Z"' % [
				x - s, y - s * 0.7, x, y - s * 1.1, x + s, y - s * 0.7, x + s * 1.05, y + s * 0.5, x, y + s * 1.1, x - s * 1.05, y + s * 0.5, x - s, y - s * 0.7], op[4])
			out += '<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s"/>' % [x - s * 0.42, y - s * 0.2, s * 0.24, s * 0.16, COL.K]
			out += '<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s"/>' % [x + s * 0.42, y - s * 0.2, s * 0.24, s * 0.16, COL.K]
			match op[5] if op.size() > 5 else "smile":
				"smile":
					out += draw(["s", "M%s %s Q%s %s %s %s" % [x - s * 0.45, y + s * 0.35, x, y + s * 0.8, x + s * 0.45, y + s * 0.35], "K", 2.2])
				"frown":
					out += draw(["s", "M%s %s Q%s %s %s %s" % [x - s * 0.4, y + s * 0.65, x, y + s * 0.25, x + s * 0.4, y + s * 0.65], "K", 2.2])
			return out
		"jester":  # jester head: x y s hat_a hat_b
			var x: float = op[1]
			var y: float = op[2]
			var s: float = op[3]
			var out := _shape('<path d="M%s %s L%s %s L%s %s Q%s %s %s %s Z"' % [x - s * 0.95, y - s * 0.15, x - s * 1.25, y - s * 0.95, x - s * 0.3, y - s * 0.65, x - s * 0.5, y - s * 0.3, x - s * 0.95, y - s * 0.15], op[4])
			out += _shape('<path d="M%s %s L%s %s L%s %s Q%s %s %s %s Z"' % [x + s * 0.95, y - s * 0.15, x + s * 1.25, y - s * 0.95, x + s * 0.3, y - s * 0.65, x + s * 0.5, y - s * 0.3, x + s * 0.95, y - s * 0.15], op[5])
			out += _shape('<path d="M%s %s L%s %s L%s %s Z"' % [x - s * 0.55, y - s * 0.4, x, y - s * 1.45, x + s * 0.55, y - s * 0.4], op[5])
			out += _shape('<circle cx="%s" cy="%s" r="%s"' % [x, y + s * 0.15, s * 0.68], "ivory")
			out += _shape('<path d="M%s %s Q%s %s %s %s L%s %s Q%s %s %s %s Z"' % [x - s * 0.8, y - s * 0.35, x, y - s * 0.75, x + s * 0.8, y - s * 0.35, x + s * 0.7, y - s * 0.15, x, y - s * 0.5, x - s * 0.7, y - s * 0.15], op[4])
			for b in [[x - s * 1.25, y - s * 0.95], [x, y - s * 1.45], [x + s * 1.25, y - s * 0.95]]:
				out += _shape('<circle cx="%s" cy="%s" r="%s"' % [b[0], b[1], s * 0.16], "gold")
			out += '<circle cx="%s" cy="%s" r="%s" fill="%s"/><circle cx="%s" cy="%s" r="%s" fill="%s"/>' % [
				x - s * 0.24, y + s * 0.1, s * 0.07, COL.K, x + s * 0.24, y + s * 0.1, s * 0.07, COL.K]
			out += draw(["s", "M%s %s Q%s %s %s %s" % [x - s * 0.3, y + s * 0.38, x, y + s * 0.62, x + s * 0.3, y + s * 0.38], "red", 2.2])
			out += '<circle cx="%s" cy="%s" r="%s" fill="%s" opacity="0.6"/><circle cx="%s" cy="%s" r="%s" fill="%s" opacity="0.6"/>' % [
				x - s * 0.45, y + s * 0.3, s * 0.1, COL.pink, x + s * 0.45, y + s * 0.3, s * 0.1, COL.pink]
			# ruff collar
			for k in 5:
				var cx := x + (k - 2) * s * 0.34
				out += _shape('<circle cx="%s" cy="%s" r="%s"' % [cx, y + s * 0.92, s * 0.2], op[4] if k % 2 == 0 else op[5])
			return out
		"crown":  # x y(base) w h fill points
			var x: float = op[1]
			var y: float = op[2]
			var w: float = op[3]
			var h: float = op[4]
			var n: int = op[6] if op.size() > 6 else 3
			var d := "M%s %s" % [x - w / 2.0, y]
			for k in n * 2 + 1:
				var t := k / float(n * 2)
				var px := x - w / 2.0 + w * t
				var py := y - h if k % 2 == 0 else y - h * 0.45
				d += " L%s %s" % [px, py]
			d += " L%s %s Z" % [x + w / 2.0, y]
			var out := _shape('<path d="%s"' % d, op[5])
			out += '<rect x="%s" y="%s" width="%s" height="%s" fill="%s" stroke="%s" stroke-width="%s"/>' % [x - w / 2.0, y - h * 0.2, w, h * 0.2, COL.bronze, COL.K, 1.6]
			for k in n + 1:
				var px := x - w / 2.0 + w * k / float(n)
				out += _shape('<circle cx="%s" cy="%s" r="%s"' % [px, y - h, h * 0.1], "ivory")
			return out
		"card":  # playing card: x y w h fill [rot] [pip kind] [pip colour]
			var x: float = op[1]
			var y: float = op[2]
			var w: float = op[3]
			var h: float = op[4]
			var rot: float = op[6] if op.size() > 6 else 0.0
			var inner := _shape('<rect x="%s" y="%s" width="%s" height="%s" rx="%s"' % [x, y, w, h, w * 0.12], op[5])
			inner += '<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="none" stroke="%s" stroke-width="0.9" opacity="0.6"/>' % [x + w * 0.12, y + w * 0.12, w * 0.76, h - w * 0.24, w * 0.06, COL.K]
			if op.size() > 7 and op[7] != "":
				inner += _shape('<path d="%s"' % _suit_d(op[7], x + w / 2.0, y + h / 2.0, w * 0.28), op[8] if op.size() > 8 else "red")
			return '<g transform="rotate(%s %s %s)">%s</g>' % [rot, x + w / 2.0, y + h / 2.0, inner]
		"flame":  # x y(base) s fill [inner]
			var x: float = op[1]
			var y: float = op[2]
			var s: float = op[3]
			var out := _shape('<path d="M%s %s C %s %s %s %s %s %s C %s %s %s %s %s %s C %s %s %s %s %s %s Z"' % [
				x, y - s * 2.1, x + s * 0.9, y - s * 1.2, x + s, y - s * 0.6, x + s * 0.8, y - s * 0.25,
				x + s * 0.5, y + s * 0.15, x - s * 0.5, y + s * 0.15, x - s * 0.8, y - s * 0.25,
				x - s * 1.1, y - s * 0.8, x - s * 0.2, y - s * 1.1, x, y - s * 2.1], op[4])
			return out + '<path d="M%s %s C %s %s %s %s %s %s C %s %s %s %s %s %s Z" fill="%s"/>' % [
				x, y - s * 1.1, x + s * 0.45, y - s * 0.6, x + s * 0.35, y - s * 0.05, x, y - s * 0.05,
				x - s * 0.35, y - s * 0.05, x - s * 0.4, y - s * 0.5, x, y - s * 1.1, COL[op[5] if op.size() > 5 else "gold"]]
		"bolt":  # lightning bolt: x y s fill
			var x: float = op[1]
			var y: float = op[2]
			var s: float = op[3]
			return _shape('<path d="M%s %s L%s %s L%s %s L%s %s L%s %s L%s %s Z"' % [
				x + s * 0.2, y - s, x - s * 0.55, y + s * 0.15, x - s * 0.05, y + s * 0.15, x - s * 0.25, y + s, x + s * 0.55, y - s * 0.2, x + s * 0.05, y - s * 0.2], op[4])
		"bottle":  # potion bottle: x y s fill (round flask)
			var x: float = op[1]
			var y: float = op[2]
			var s: float = op[3]
			# a round flask: neck, then a full circle of glass
			var out := _shape('<path d="M%s %s L%s %s A%s %s 0 1 0 %s %s L%s %s Z"' % [
				x - s * 0.22, y - s, x - s * 0.22, y - s * 0.4, s * 0.72, s * 0.72, x + s * 0.22, y - s * 0.4, x + s * 0.22, y - s], "white")
			out += '<path d="M%s %s A%s %s 0 0 0 %s %s Z" fill="%s"/>' % [x - s * 0.66, y + s * 0.1, s * 0.66, s * 0.66, x + s * 0.66, y + s * 0.1, COL[op[4]]]
			out += _shape('<rect x="%s" y="%s" width="%s" height="%s" rx="1"' % [x - s * 0.3, y - s * 1.18, s * 0.6, s * 0.24], "bronze")
			return out + draw(["hi", x - s * 0.3, y - s * 0.1, s * 0.12])
		"skull":  # x y s
			var x: float = op[1]
			var y: float = op[2]
			var s: float = op[3]
			var out := _shape('<path d="M%s %s Q%s %s %s %s Q%s %s %s %s Q%s %s %s %s L%s %s Z"' % [
				x - s * 0.45, y + s * 0.85, x - s * 1.05, y + s * 0.4, x - s * 0.95, y - s * 0.2, x - s * 0.8, y - s * 1.05, x + s * 0.95, y - s * 0.2,
				x + s * 1.05, y + s * 0.4, x + s * 0.45, y + s * 0.85, x - s * 0.45, y + s * 0.85], "ivory")
			out += '<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s"/><ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s"/>' % [
				x - s * 0.38, y + s * 0.05, s * 0.24, s * 0.28, COL.K, x + s * 0.38, y + s * 0.05, s * 0.24, s * 0.28, COL.K]
			out += '<path d="M%s %s L%s %s L%s %s Z" fill="%s"/>' % [x, y + s * 0.35, x - s * 0.12, y + s * 0.55, x + s * 0.12, y + s * 0.55, COL.K]
			for k in 3:
				out += draw(["l", x + (k - 1) * s * 0.22, y + s * 0.7, x + (k - 1) * s * 0.22, y + s * 0.88, "K", 1.4])
			return out
		"eye":  # x y s iris
			var x: float = op[1]
			var y: float = op[2]
			var s: float = op[3]
			var out := _shape('<path d="M%s %s Q%s %s %s %s Q%s %s %s %s Z"' % [x - s, y, x, y - s * 0.75, x + s, y, x, y + s * 0.75, x - s, y], "white")
			out += _shape('<circle cx="%s" cy="%s" r="%s"' % [x, y, s * 0.38], op[4])
			return out + '<circle cx="%s" cy="%s" r="%s" fill="%s"/>' % [x, y, s * 0.16, COL.K] + draw(["hi", x - s * 0.14, y - s * 0.16, s * 0.08])
		"moon":  # crescent: x y r fill (opening right)
			var x: float = op[1]
			var y: float = op[2]
			var r: float = op[3]
			return _shape('<path d="M%s %s A%s %s 0 1 0 %s %s A%s %s 0 0 1 %s %s Z"' % [x + r * 0.35, y - r * 0.94, r, r, x + r * 0.35, y + r * 0.94, r * 0.8, r * 0.8, x + r * 0.35, y - r * 0.94], op[4])
		"die":  # x y s pips [rot] [fill]
			var x: float = op[1]
			var y: float = op[2]
			var s: float = op[3]
			var n: int = op[4]
			var rot: float = op[5] if op.size() > 5 else 0.0
			var inner := _shape('<rect x="%s" y="%s" width="%s" height="%s" rx="%s"' % [x - s, y - s, s * 2, s * 2, s * 0.35], op[6] if op.size() > 6 else "white")
			var spots := {1: [[0, 0]], 2: [[-1, -1], [1, 1]], 3: [[-1, -1], [0, 0], [1, 1]], 4: [[-1, -1], [1, -1], [-1, 1], [1, 1]],
				5: [[-1, -1], [1, -1], [0, 0], [-1, 1], [1, 1]], 6: [[-1, -1], [1, -1], [-1, 0], [1, 0], [-1, 1], [1, 1]]}
			for p in spots[n]:
				inner += '<circle cx="%s" cy="%s" r="%s" fill="%s"/>' % [x + p[0] * s * 0.5, y + p[1] * s * 0.5, s * 0.16, COL.K]
			return '<g transform="rotate(%s %s %s)">%s</g>' % [rot, x, y, inner]
		"bag":  # money sack: x y s fill
			var x: float = op[1]
			var y: float = op[2]
			var s: float = op[3]
			var out := _shape('<path d="M%s %s Q%s %s %s %s Q%s %s %s %s Q%s %s %s %s Q%s %s %s %s Z"' % [
				x - s * 0.3, y - s * 0.75, x - s * 1.1, y - s * 0.1, x - s * 0.9, y + s * 0.6, x, y + s * 1.05, x + s * 0.9, y + s * 0.6, x + s * 1.1, y - s * 0.1,
				x + s * 0.3, y - s * 0.75, x, y - s * 0.6, x - s * 0.3, y - s * 0.75], op[4])
			out += _shape('<path d="M%s %s L%s %s L%s %s L%s %s Z"' % [x - s * 0.35, y - s * 0.75, x - s * 0.5, y - s * 1.05, x + s * 0.5, y - s * 1.05, x + s * 0.35, y - s * 0.75], op[4])
			return out + draw(["l", x - s * 0.38, y - s * 0.75, x + s * 0.38, y - s * 0.75, "gold", 2.4])
		"glass":  # magnifying lens, see-through: x y r
			var out := '<circle cx="%s" cy="%s" r="%s" fill="%s" fill-opacity="0.3"/>' % [op[1], op[2], op[3], COL.sky]
			out += '<circle cx="%s" cy="%s" r="%s" fill="none" stroke="%s" stroke-width="%s"/>' % [op[1], op[2], op[3], COL.K, STROKE + 4]
			out += '<circle cx="%s" cy="%s" r="%s" fill="none" stroke="%s" stroke-width="3"/>' % [op[1], op[2], op[3], COL.gold]
			return out + draw(["hi", op[1] - op[3] * 0.45, op[2] - op[3] * 0.45, op[3] * 0.18])
		"veil":  # sheer cloth on a rod, scalloped lace hem: x0 x1 y0 y1
			var x0: float = op[1]
			var x1: float = op[2]
			var y0: float = op[3]
			var y1: float = op[4]
			var d := "M%s %s L%s %s L%s %s" % [x0, y0, x1, y0, x1 + 4, y1]
			var n := maxi(3, int((x1 - x0 + 8) / 10.0))
			var step := (x1 - x0 + 8) / n
			for k in n:
				var xa := x1 + 4 - step * k
				d += " Q%s %s %s %s" % [xa - step / 2.0, y1 + 6, xa - step, y1]
			d += " Z"
			var out := '<path d="%s" fill="%s" fill-opacity="0.55" stroke="%s" stroke-width="1.8" stroke-linejoin="round"/>' % [d, COL.sky, COL.K]
			for k in [0.3, 0.55, 0.8]:
				var fx: float = x0 + (x1 - x0) * k
				out += draw(["s", "M%s %s Q%s %s %s %s" % [fx, y0 + 4, fx - 3, (y0 + y1) / 2.0, fx + 2, y1 - 2], "white", 1.4])
			out += draw(["l", x0 - 6, y0, x1 + 6, y0, "K", 6]) + draw(["l", x0 - 6, y0, x1 + 6, y0, "gold", 3])
			return out + _shape('<circle cx="%s" cy="%s" r="3.5"' % [x0 - 7, y0], "gold") + _shape('<circle cx="%s" cy="%s" r="3.5"' % [x1 + 7, y0], "gold")
		"key":  # old key hanging from its bow: x y(bow centre) s fill [rot]
			var x: float = op[1]
			var y: float = op[2]
			var s: float = op[3]
			var inner := _shape('<rect x="%s" y="%s" width="%s" height="%s" rx="1"' % [x - s * 0.12, y + s * 0.3, s * 0.24, s * 1.5], op[4])
			inner += _shape('<path d="M%s %s h%s v%s h%s v%s h%s v%s h%s Z"' % [x + s * 0.12, y + s * 1.3, s * 0.4, s * 0.16, -s * 0.18, s * 0.12, s * 0.24, s * 0.18, -s * 0.46], op[4])
			inner += _shape('<circle cx="%s" cy="%s" r="%s"' % [x, y, s * 0.38], op[4])
			inner += '<circle cx="%s" cy="%s" r="%s" fill="%s"/>' % [x, y, s * 0.15, COL.K]
			return '<g transform="rotate(%s %s %s)">%s</g>' % [op[5] if op.size() > 5 else 0, x, y - s * 0.4, inner]
		"rails":  # railway track running into the distance: x(centre) y0(far) y1(near) w(near)
			var x: float = op[1]
			var y0: float = op[2]
			var y1: float = op[3]
			var w: float = op[4]
			var out := ""
			for k in 5:
				var t := k / 4.0
				var yy: float = lerpf(y0 + 4, y1 - 2, t * t)
				var hw: float = lerpf(w * 0.18, w * 0.62, t * t)
				out += draw(["l", x - hw, yy, x + hw, yy, "brown", lerpf(2.0, 5.0, t)])
			out += draw(["l", x - w * 0.12, y0, x - w * 0.5, y1, "slate", 3.2]) + draw(["l", x + w * 0.12, y0, x + w * 0.5, y1, "slate", 3.2])
			return out
		"wave":  # rolling wave band: y x0 x1 fill
			var y: float = op[1]
			var x0: float = op[2]
			var x1: float = op[3]
			var d := "M%s %s" % [x0, y + 14]
			var x := x0
			while x < x1:
				d += " Q%s %s %s %s" % [x + 5, y - 6, x + 10, y]
				x += 10
			d += " L%s %s Z" % [x1, y + 14]
			return _shape('<path d="%s"' % d, op[4])
		"leaf":  # x y s rot fill
			var x: float = op[1]
			var y: float = op[2]
			var s: float = op[3]
			var inner := _shape('<path d="M%s %s Q%s %s %s %s Q%s %s %s %s Z"' % [x, y + s, x - s * 0.8, y, x, y - s, x + s * 0.8, y, x, y + s], op[5])
			inner += draw(["l", x, y + s * 0.8, x, y - s * 0.6, "K", 1.2])
			return '<g transform="rotate(%s %s %s)">%s</g>' % [op[4], x, y, inner]
		"clover":  # four-leaf clover: x y s fill
			var x: float = op[1]
			var y: float = op[2]
			var s: float = op[3]
			var out := draw(["s", "M%s %s Q%s %s %s %s" % [x, y, x + s * 0.3, y + s * 0.9, x + s * 0.7, y + s * 1.2], "green", 3])
			for a in [0, 90, 180, 270]:
				out += '<g transform="rotate(%s %s %s)">%s</g>' % [a, x, y, _shape('<path d="M%s %s C %s %s %s %s %s %s C %s %s %s %s %s %s Z"' % [
					x, y, x - s * 0.75, y - s * 0.5, x - s * 0.45, y - s * 1.05, x, y - s * 0.65, x + s * 0.45, y - s * 1.05, x + s * 0.75, y - s * 0.5, x, y], op[4])]
			return out
	push_warning("CharmSVG: unknown op %s" % op[0])
	return ""


static func _shape(open_tag: String, fill: String) -> String:
	return '%s fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round"/>' % [open_tag, COL[fill], COL.K, STROKE]


static func _rot(op: Array, idx: int, cx: float, cy: float) -> String:
	if op.size() > idx and op[idx] != 0:
		return ' transform="rotate(%s %s %s)"' % [op[idx], cx, cy]
	return ""


static func _star_d(x: float, y: float, r: float, n: int, inner: float) -> String:
	var pts := []
	for k in n * 2:
		var a := deg_to_rad(-90 + k * 180.0 / n)
		var rr := r if k % 2 == 0 else r * inner
		pts.append("%s %s" % [x + cos(a) * rr, y + sin(a) * rr])
	return "M" + " L".join(pts) + " Z"


static func _suit_d(kind: String, x: float, y: float, s: float) -> String:
	match kind:
		"heart":
			return "M%s %s C %s %s %s %s %s %s C %s %s %s %s %s %s Z" % [x, y + s, x - s * 1.6, y - s * 0.1, x - s * 0.8, y - s * 1.3, x, y - s * 0.45,
				x + s * 0.8, y - s * 1.3, x + s * 1.6, y - s * 0.1, x, y + s]
		"diamond":
			return "M%s %s L%s %s L%s %s L%s %s Z" % [x, y - s, x + s * 0.72, y, x, y + s, x - s * 0.72, y]
		"spade":
			return "M%s %s C %s %s %s %s %s %s C %s %s %s %s %s %s Z M%s %s L%s %s L%s %s Z" % [
				x, y - s, x + s * 1.5, y + s * 0.05, x + s * 0.7, y + s * 0.95, x, y + s * 0.35,
				x - s * 0.7, y + s * 0.95, x - s * 1.5, y + s * 0.05, x, y - s, x, y + s * 0.2, x + s * 0.35, y + s, x - s * 0.35, y + s]
		"club":
			var r := s * 0.44
			return ("M%s %s a%s %s 0 1 0 0.01 0 Z M%s %s a%s %s 0 1 0 0.01 0 Z M%s %s a%s %s 0 1 0 0.01 0 Z M%s %s L%s %s L%s %s Z") % [
				x - r, y - s * 0.45, r, r, x - s * 0.48 - r, y + s * 0.15, r, r, x + s * 0.48 - r, y + s * 0.15, r, r,
				x, y, x + s * 0.32, y + s, x - s * 0.32, y + s]
	return ""
