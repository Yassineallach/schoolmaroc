class_name DeckArt
extends RefCounted

## Aleatro's pixel deck. Every face is painted into a 50x70 image (shown at
## 2x with nearest filtering) and cached as a texture:
## - corner index: pixel rank over a small suit, repeated upside down in the
##   opposite corner
## - 2-10: traditional pip layouts, pips past the middle turned upside down
## - ace: one large pip
## - J / Q / K: double-ended court figures, seen side-on, from hand-drawn
##   templates plus a sash and a held item, coloured per suit
## The face itself (paper colour, enhancement tint) is drawn by CardView
## underneath, so these images are transparent apart from the ink.

const W := 50
const H := 70

# ---------------------------------------------------------------- palette

const INK := Color("22243a")
const CREAM := Color("fff6e0")
const GOLD := Color("f5b82e")
const GOLD_DARK := Color("b8801a")
const SKIN := Color("f4cfae")
const SKIN_SHADE := Color("d9a07a")
const STEEL := Color("c9d3dc")
const STEEL_DARK := Color("8a96a3")
const ROSE := Color("e63946")
# Second colour of each suit's court robes: spade, heart, club, diamond.
const ACCENTS := [Color("e63946"), Color("1d6fd1"), Color("f2b415"), Color("3f9a5a")]
const HAIR := {11: Color("7a4a2a"), 12: Color("b5462e"), 13: Color("dfe3ea")}
const HAIR_SHADE := {11: Color("553220"), 12: Color("82301f"), 13: Color("a9b0bd")}

# ---------------------------------------------------------------- glyphs

## 3x5 rank glyphs ("1" is 2 wide, for 10).
const GLYPHS := {
	"A": [".#.", "#.#", "###", "#.#", "#.#"],
	"2": ["##.", "..#", ".#.", "#..", "###"],
	"3": ["##.", "..#", ".#.", "..#", "##."],
	"4": ["..#", ".##", "#.#", "###", "..#"],
	"5": ["###", "#..", "##.", "..#", "##."],
	"6": [".##", "#..", "##.", "#.#", ".#."],
	"7": ["###", "..#", ".#.", ".#.", ".#."],
	"8": [".#.", "#.#", ".#.", "#.#", ".#."],
	"9": [".#.", "#.#", ".##", "..#", "##."],
	"1": [".#", "##", ".#", ".#", ".#"],
	"0": [".#.", "#.#", "#.#", "#.#", ".#."],
	"J": ["..#", "..#", "..#", "#.#", ".#."],
	"Q": [".#.", "#.#", "#.#", "##.", ".##"],
	"K": ["#.#", "#.#", "##.", "#.#", "#.#"],
}

## 5x5 corner suits: spade, heart, club, diamond.
const SMALL := [
	["..#..", ".###.", "#####", "..#..", ".###."],
	[".#.#.", "#####", "#####", ".###.", "..#.."],
	[".###.", ".###.", "##.##", "#####", "..#.."],
	["..#..", ".###.", "#####", ".###.", "..#.."],
]

## 7x7 pips: spade, heart, club, diamond.
const PIPS := [
	["...#...", "..###..", ".#####.", "#######", "#######", "...#...", "..###.."],
	[".##.##.", "#######", "#######", "#######", ".#####.", "..###..", "...#..."],
	["..###..", ".#####.", "..###..", "##.#.##", "#######", "##.#.##", "..###.."],
	["...#...", "..###..", ".#####.", "#######", ".#####.", "..###..", "...#..."],
]

## Pip centres (x, y) per rank; pips below the middle are drawn upside down.
const L := 16
const C := 25
const R := 34
const LAYOUTS := {
	2: [[C, 14], [C, 56]],
	3: [[C, 14], [C, 35], [C, 56]],
	4: [[L, 14], [R, 14], [L, 56], [R, 56]],
	5: [[L, 14], [R, 14], [C, 35], [L, 56], [R, 56]],
	6: [[L, 14], [R, 14], [L, 35], [R, 35], [L, 56], [R, 56]],
	7: [[L, 14], [R, 14], [C, 24], [L, 35], [R, 35], [L, 56], [R, 56]],
	8: [[L, 14], [R, 14], [C, 24], [L, 35], [R, 35], [C, 46], [L, 56], [R, 56]],
	9: [[L, 14], [R, 14], [L, 28], [R, 28], [C, 35], [L, 42], [R, 42], [L, 56], [R, 56]],
	10: [[L, 14], [R, 14], [C, 21], [L, 28], [R, 28], [L, 42], [R, 42], [C, 49], [L, 56], [R, 56]],
}

static var _cache := {}


## The face texture for `rank` (2-14) of `suit` (0 spade, 1 heart, 2 club, 3 diamond).
static func face(rank: int, suit: int) -> ImageTexture:
	var key := rank * 4 + suit
	if not _cache.has(key):
		_cache[key] = ImageTexture.create_from_image(paint(rank, suit))
	return _cache[key]


## The face as an Image, for tools and previews.
static func paint(rank: int, suit: int) -> Image:
	var img := Image.create(W, H, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	var col: Color = Data.SUIT_COLORS[suit]
	_index(img, rank, suit, col)
	if rank == 14:
		_big_pip(img, suit, col)
	elif rank >= 11:
		_court(img, rank, suit, col)
	else:
		for p in LAYOUTS[rank]:
			_bitmap(img, PIPS[suit], p[0] - 3, p[1] - 3, col, p[1] > 35)
	return img


# ---------------------------------------------------------------- pieces

static func _bitmap(img: Image, rows: Array, x0: int, y0: int, col: Color, flip := false) -> void:
	var h := rows.size()
	for y in h:
		var row: String = rows[h - 1 - y] if flip else rows[y]
		for x in row.length():
			if row[x] == "#":
				img.set_pixel(x0 + x, y0 + y, col)


static func _index(img: Image, rank: int, suit: int, col: Color) -> void:
	var label: String = Data.RANK_LABELS[rank]
	var x := 2
	for ch in label:
		_bitmap(img, GLYPHS[ch], x, 3, col)
		x += GLYPHS[ch][0].length() + 1
	var width := x - 3
	var sx := 2 + (width - 5) / 2 if width > 5 else 1
	_bitmap(img, SMALL[suit], sx, 10, col)
	# the same index, upside down in the opposite corner
	for y in 16:
		for xx in 9:
			var c := img.get_pixel(xx, y)
			if c.a > 0.0:
				img.set_pixel(W - 1 - xx, H - 1 - y, c)


## A large pip, rasterised from the suit's shape, with a one-pixel
## darker rim on its lower edge.
static func _big_pip(img: Image, suit: int, col: Color) -> void:
	const S := 19
	var x0 := C - S / 2
	var y0 := 35 - S / 2
	for y in S:
		for x in S:
			var p := Vector2((x + 0.5) / S - 0.5, (y + 0.5) / S - 0.5)
			if _in_suit(suit, p):
				var below := Vector2(p.x, p.y + 1.0 / S)
				img.set_pixel(x0 + x, y0 + y, col if _in_suit(suit, below) else col.darkened(0.35))


## Whether point `p` (unit square, centred) lies inside the suit shape.
static func _in_suit(suit: int, p: Vector2) -> bool:
	match suit:
		1:
			return p.distance_to(Vector2(-0.24, -0.14)) < 0.26 or p.distance_to(Vector2(0.24, -0.14)) < 0.26 \
				or _in_tri(p, Vector2(-0.49, -0.04), Vector2(0.49, -0.04), Vector2(0, 0.5))
		3:
			return absf(p.x) / 0.4 + absf(p.y) / 0.5 <= 1.0
		0:
			return p.distance_to(Vector2(-0.23, 0.1)) < 0.25 or p.distance_to(Vector2(0.23, 0.1)) < 0.25 \
				or _in_tri(p, Vector2(-0.48, 0.06), Vector2(0, -0.5), Vector2(0.48, 0.06)) \
				or _in_tri(p, Vector2(0, 0.1), Vector2(0.17, 0.5), Vector2(-0.17, 0.5))
		_:
			return p.distance_to(Vector2(0, -0.24)) < 0.22 or p.distance_to(Vector2(-0.24, 0.08)) < 0.22 \
				or p.distance_to(Vector2(0.24, 0.08)) < 0.22 \
				or _in_tri(p, Vector2(0, -0.05), Vector2(0.17, 0.5), Vector2(-0.17, 0.5))


static func _in_tri(p: Vector2, a: Vector2, b: Vector2, c: Vector2) -> bool:
	var d1 := (p - b).cross(a - b)
	var d2 := (p - c).cross(b - c)
	var d3 := (p - a).cross(c - a)
	return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))


# ---------------------------------------------------------------- courts

## Court half-figures, drawn as the left half (column 15 is the centre) and
## mirrored; the sash and held item are painted over them afterwards.
##   K ink  S skin  s skin shade  r lips/cheek  H hair  h hair shade
##   P robe  p robe shade  A accent  a accent shade  G gold  g dark gold
##   W cream  J jewel
const JACK := [
	"................",
	"...........KKKKK",
	"..........KPPPPP",
	".........KPPPPPP",
	"........KPPPPPPP",
	"........KGGGGGGG",
	"........KHHHHHHH",
	"........KHSSSSSS",
	"........KHShhSSS",
	"........KHSKWSSS",
	"........KHSSSSSs",
	"........KHrSSSSs",
	".........KSSSSrr",
	"................",
	"....KKKKKKKKKKKK",
	"...KAAAAAaaAAAAA",
	"..KpPPPPAaAAAAAA",
	".KppPpPpPAaaaaaa",
	"KppPpPpPpPpPpPpG",
	"KppPpPpPpPpPpPpg",
	"KppPpPpPpPpPpPpG",
	"KpAAAPpPpPpPpPpg",
	"KSSSKPpPpPpPpPpG",
	"KsSSKPpPpPpPpPpg",
	".KKKPpPpPpPpPpPG",
	"..KpPpPpPpPpPpPg",
	"..KpPpPpPpPpPpPG",
	"..KgggggggggggGA",
	"..KpPpPpPpPpPpPg",
	"..KpPpPpPpPpPpPG",
]
const QUEEN := [
	"................",
	"............G..J",
	"...........GGG.G",
	"..........KGgGGG",
	".........KHHHHHH",
	"........KHHHHHHH",
	"........KHSSSSSS",
	"........KHShSSSS",
	"........KHSKWSSS",
	"........KHSSSSSs",
	"........KHrSSSSs",
	"........KHSSSSrr",
	"........KHHSSSSS",
	"....KKKKKKKKKKKK",
	"...KWWWKWWWWWWWW",
	"..KWAWAWWAWAWAWW",
	".KpPPPPPPKWWWWWW",
	"KppPAPPPPKPKWWAW",
	"KppPPPPAPKPPKWWW",
	"KppPAPPPPPAPPKKW",
	"KppPPPPAPPPPAPPK",
	"KpGGGPPPPPAPPPPG",
	"KSSSKPPAPPPPAPPg",
	"KsSSKPPPPPAPPPPG",
	".KKKPPPAPPPPAPPg",
	"..KpPPPPPPAPPPPG",
	"..KpPPPAPPPPAPPg",
	"..KgggggggggggGA",
	"..KpPPPPPPPPPPPW",
	"..KpPPpPPpPPpPPW",
]
const KING := [
	"..........G....G",
	"..........G..G.G",
	"..........GG.GGG",
	"..........GGGGGG",
	"..........GJGAGJ",
	".........KgggggG",
	".........KHHHHHH",
	".........KSSSSSS",
	".........KShhSSS",
	".........KSKWSSS",
	".........KSSSSSs",
	".........KrSSSSs",
	"....KKKKKKKKKKKK",
	"...KWWKWWKWWKWWW",
	"..KWKWWKWWKWWKWW",
	".KpPPPPPKWWKWWWW",
	".KpPpPPpPKWWKWWW",
	"KppPPPPPPPKKWWKW",
	"KppPpPPpPPPPKKWW",
	"KppPPPPPPPpPPPKW",
	"KppPpPPpPPPPpPPG",
	"KpGGGPPPPPpPPPPg",
	"KSSSKPpPPpPPpPPG",
	"KsSSKPPPPPPPPPPg",
	".KKKPpPPpPPpPPpG",
	"..KpPPPPPPPPPPPg",
	"..KpPpPPpPPpPPpG",
	"..KgggggggggggGJ",
	"..KpPPpPPpPPpPPG",
	"..KpPPpPPpPPpPPg",
]

## Side-on heads, full width, drawn over the mirrored half: rows 0-11
## replace it outright, rows 12-13 only where they are not ".". No eyes.
const JACK_HEAD := [
	"...............................",
	"...........KKKKKKKK............",
	"..........KPPPPPPPPK...........",
	".........KPPPPPPPPPPK..........",
	".........KGGGGGGGGGGGKK........",
	".........KHHHHSSSSSSK..........",
	".........KHHHSSSSSSSK..........",
	".........KHHHSSSSSSSSK.........",
	".........KHHhSSSSSSSsK.........",
	".........KHHhSSSSSSSK..........",
	".........KHHhSSSSSrSK..........",
	"..........KHhSSSSSSK...........",
	"...........KKSSSSKK............",
	"............KSSSSK.............",
]
const QUEEN_HEAD := [
	"...............................",
	"............G..J..G............",
	"...........GGG.GGG.GGG.........",
	"..........KGgGGgGGgGK..........",
	".........KHHHHHHHHHHK..........",
	"........KHHHHHHSSSSSK..........",
	".......KHHHHHHSSSSSSK..........",
	".......KHHhHHHSSSSSSSK.........",
	"......KHHHhHHhSSSSSSsK.........",
	"......KHHHhHHhSSSSSrK..........",
	".......KHHhHHhSSSSSSK..........",
	"........KKKHHhKSSSSK...........",
	"............KKSSK..............",
	"............KSSSK..............",
]
const KING_HEAD := [
	"..........G..G..G..G...........",
	"..........GG.GG.GG.GG..........",
	"..........GGGGGGGGGGG..........",
	"..........GJGGAGGJGGG..........",
	".........KgggggggggggK.........",
	".........KHHHHHSSSSSSK.........",
	".........KHHHHSSSSSSSK.........",
	".........KHHHhSSSSSSSSK........",
	".........KHHHhSSSSSSSsK........",
	".........KHHHhSSSSHHHHK........",
	".........KHHHhHHHHHHrK.........",
	".........KHHHhHHHHHHHK.........",
	"..........KHHhHHHHHHHHK........",
	"............KhHHHHHHHK.........",
]

const HW := 31  # court half width
const HH := 30  # court half height; the last row meets the upside-down half
const X0 := 10
const Y0 := 5

## What each court holds, by rank (J, Q, K) and suit.
const ITEMS := [
	["spear", "horn", "staff", "coin"],
	["mirror", "rose", "fan", "mirror"],
	["sword", "axe", "scepter", "orb"],
]


## A court card: the half figure in the top half of the frame, then the
## same half turned upside down below, like a real double-ended card.
static func _court(img: Image, rank: int, suit: int, col: Color) -> void:
	var half: Array = [JACK, QUEEN, KING][rank - 11]
	var head: Array = [JACK_HEAD, QUEEN_HEAD, KING_HEAD][rank - 11]
	var g: Array = []
	for row in half:
		var full: String = row + row.left(15).reverse()
		g.append(_chars(full))
	for y in head.size():
		var row: String = head[y]
		for x in HW:
			if y < 12 or row[x] != ".":
				g[y][x] = row[x]
	_overlay(g, rank - 11, suit)
	# hearts and diamonds face the other way
	if suit == 1 or suit == 3:
		for row in g:
			row.reverse()
	var pal := _palette(rank, suit, col)
	for y in HH:
		for x in HW:
			var ch: String = g[y][x]
			if ch == ".":
				continue
			var c: Color = pal[ch]
			img.set_pixel(X0 + x, Y0 + y, c)
			img.set_pixel(50 - (X0 + x), 69 - (Y0 + y), c)


static func _chars(s: String) -> Array:
	var out: Array = []
	for i in s.length():
		out.append(s[i])
	return out


static func _palette(rank: int, suit: int, col: Color) -> Dictionary:
	var a: Color = ACCENTS[suit]
	return {
		"K": INK, "W": CREAM, "G": GOLD, "g": GOLD_DARK, "S": SKIN, "s": SKIN_SHADE,
		"r": Color("e2786e"), "J": ROSE, "L": STEEL, "l": STEEL_DARK,
		"P": col, "p": col.darkened(0.35), "A": a, "a": a.darkened(0.3),
		"H": HAIR[rank], "h": HAIR_SHADE[rank],
	}


## Sash, the jack's feather and the held item, over the mirrored half.
static func _overlay(g: Array, court: int, suit: int) -> void:
	var put := func(x: int, y: int, c: String) -> void:
		if x >= 0 and x < HW and y >= 0 and y < HH and g[y][x] != ".":
			g[y][x] = c
	var force := func(x: int, y: int, c: String) -> void:
		if x >= 0 and x < HW and y >= 0 and y < HH:
			g[y][x] = c
	# sash: left shoulder down to the right hip, gold edges, accent middle
	for y in range(15, HH):
		var x := 5 + roundi((y - 15) * 1.45)
		for e in [[-2, "G"], [-1, "A"], [0, "A"], [1, "a"], [2, "G"]]:
			if not ("KSsWHhr.".contains(g[y][x + e[0]])):
				put.call(x + e[0], y, e[1])
	# the jack's cap feather sweeps back over the top
	if court == 0:
		for q in [[20, 3, "A"], [21, 2, "A"], [22, 2, "A"], [23, 1, "A"], [24, 1, "A"], [25, 0, "A"],
				[21, 3, "a"], [22, 3, "a"], [23, 2, "a"], [24, 2, "a"]]:
			force.call(q[0], q[1], q[2])
	var kind: String = ITEMS[court][suit]
	var hx := 27
	var hy := 22
	if kind in ["sword", "spear", "staff", "scepter", "axe"]:
		var top: int = {"sword": 1, "spear": 0, "staff": 2, "scepter": 2, "axe": 3}[kind]
		var shaft: String = {"sword": "L", "spear": "g", "staff": "g", "scepter": "G", "axe": "g"}[kind]
		for y in range(top, 29):
			force.call(hx, y, shaft)
			force.call(hx + 1, y, "K" if kind != "sword" or y > hy - 3 else "l")
		force.call(hx - 1, top, "K")
		force.call(hx + 2, top, "K")
		match kind:
			"sword":
				for x in range(hx - 2, hx + 3):
					force.call(x, hy - 2, "G")
				force.call(hx, hy - 1, "g")
				force.call(hx, 0, "L")
			"spear":
				for y in 3:
					force.call(hx, y, "L")
				force.call(hx - 1, 2, "l")
				force.call(hx + 1, 2, "l")
				force.call(hx - 1, 4, "A")
				force.call(hx + 1, 4, "A")
			"axe":
				for y in range(3, 9):
					for x in range(hx - 4, hx):
						force.call(x, y, "L" if x > hx - 4 else "l")
				force.call(hx - 5, 5, "l")
				force.call(hx - 5, 6, "l")
			"scepter":
				for q in [[0, -2], [-1, -1], [0, -1], [1, -1], [0, 0]]:
					force.call(hx + q[0], top + q[1], "G")
				force.call(hx, top - 1, "A")
			"staff":
				force.call(hx - 1, 1, "A")
				force.call(hx + 1, 1, "A")
				force.call(hx, 0, "A")
				force.call(hx, 1, "a")
		return
	match kind:
		"rose":
			for y in range(hy - 7, hy + 1):
				force.call(hx, y, "a" if suit != 3 else "p")
			for q in [[0, -10], [-1, -9], [0, -9], [1, -9], [-1, -8], [0, -8], [1, -8]]:
				force.call(hx + q[0], hy + q[1], "J")
			force.call(hx + 1, hy - 5, "a")
		"mirror":
			for y in range(hy - 4, hy + 1):
				force.call(hx, y, "g")
			for q in [[0, -8], [-1, -7], [1, -7], [-1, -6], [1, -6], [0, -5]]:
				force.call(hx + q[0], hy + q[1], "G")
			force.call(hx, hy - 7, "W")
			force.call(hx, hy - 6, "L")
		"fan":
			for i in 5:
				for y in range(hy - 7 + absi(i - 2), hy):
					force.call(hx - 2 + i, y, "A" if i % 2 == 0 else "W")
			force.call(hx, hy, "g")
		"horn":
			for q in [[-1, -1], [0, -2], [1, -3], [2, -4], [2, -5], [2, -6]]:
				force.call(hx + q[0], hy + q[1], "G")
			for x in range(hx + 1, hx + 4):
				force.call(x, hy - 7, "g")
		"coin":
			for q in [[0, -1], [-1, 0], [0, 0], [1, 0], [0, 1]]:
				force.call(hx + q[0], hy - 3 + q[1], "G")
			force.call(hx, hy - 3, "g")
		"orb":
			for q in [[0, -1], [-1, 0], [0, 0], [1, 0], [0, 1], [-1, -1], [1, -1], [-1, 1], [1, 1]]:
				force.call(hx + q[0], hy - 3 + q[1], "G")
			force.call(hx, hy - 3, "A")
			for q in [[0, -6], [-1, -5], [0, -5], [1, -5]]:
				force.call(hx + q[0], hy + q[1], "G")
