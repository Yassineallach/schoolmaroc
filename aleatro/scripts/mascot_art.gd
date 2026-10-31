class_name MascotArt
extends RefCounted

## Ace, drawn pixel by pixel in code (no image assets): a living Ace of Hearts
## in a two-pointed jester cap, red and blue with gold bells. 30x44 art
## pixels, shown at 4x with no smoothing. Frames: eyes open or shut, mouth
## shut, half open or open. Everything opaque gets a dark outline.

const GW := 30
const GH := 44
const SCALE := 4

const INK := Color("2b2d42")
const CARD := Color("f7f3ea")
const SHADE := Color("e3dccb")
const RED := Color("e63946")
const RED_DARK := Color("b3364e")
const BLUE := Color("2f6fd1")
const BLUE_DARK := Color("1f4a99")
const GOLD := Color("ffdf6b")
const GOLD_DARK := Color("d9a521")
const CHEEK := Color("f4a6a6")
const MOUTH := Color("7a1f2b")
const TONGUE := Color("e85d75")

static var _frames := {}  # "eyes_mouth" -> ImageTexture


## The frame for eyes open (or shut) and mouth 0 shut, 1 half, 2 open.
static func frame(eyes_open: bool, mouth: int) -> Texture2D:
	var key := "%s_%d" % [eyes_open, mouth]
	if not _frames.has(key):
		_frames[key] = ImageTexture.create_from_image(_draw(eyes_open, mouth))
	return _frames[key]


static func _draw(eyes_open: bool, mouth: int) -> Image:
	var im := Image.create(GW, GH, false, Image.FORMAT_RGBA8)
	im.fill(Color(0, 0, 0, 0))
	_card(im)
	_cap(im)
	_face(im, eyes_open, mouth)
	_outline(im)
	return im


static func _rect(im: Image, x: int, y: int, w: int, h: int, c: Color) -> void:
	for yy in range(y, y + h):
		for xx in range(x, x + w):
			if xx >= 0 and yy >= 0 and xx < GW and yy < GH:
				im.set_pixel(xx, yy, c)


static func _px(im: Image, pts: Array, c: Color) -> void:
	for p in pts:
		im.set_pixel(p.x, p.y, c)


## A filled triangle, by testing each pixel's centre.
static func _tri(im: Image, a: Vector2, b: Vector2, c: Vector2, col: Color) -> void:
	for y in GH:
		for x in GW:
			var p := Vector2(x + 0.5, y + 0.5)
			var d1 := (p - b).cross(a - b)
			var d2 := (p - c).cross(b - c)
			var d3 := (p - a).cross(c - a)
			var neg := d1 < 0 or d2 < 0 or d3 < 0
			var pos := d1 > 0 or d2 > 0 or d3 > 0
			if not (neg and pos):
				im.set_pixel(x, y, col)


static func _card(im: Image) -> void:
	# the card: x 3..26, y 10..42, corners clipped, shaded right and bottom
	_rect(im, 3, 11, 24, 31, CARD)
	_rect(im, 4, 10, 22, 33, CARD)
	_rect(im, 25, 12, 1, 29, SHADE)
	_rect(im, 5, 41, 20, 1, SHADE)
	# corner index: a red "A" over a little heart
	_px(im, [Vector2i(7, 13), Vector2i(6, 14), Vector2i(8, 14), Vector2i(6, 15), Vector2i(7, 15), Vector2i(8, 15),
			Vector2i(6, 16), Vector2i(8, 16), Vector2i(6, 17), Vector2i(8, 17)], RED)
	_px(im, [Vector2i(6, 19), Vector2i(8, 19), Vector2i(6, 20), Vector2i(7, 20), Vector2i(8, 20), Vector2i(7, 21)], RED)
	# the big heart on his belly
	var heart := [
		"..RR.RR..",
		".RRRRRRR.",
		".RRRRRRR.",
		"..RRRRR..",
		"...RRR...",
		"....R....",
	]
	for r in heart.size():
		for k in heart[r].length():
			if heart[r][k] == "R":
				im.set_pixel(11 + k, 33 + r, RED)
	im.set_pixel(13, 34, Color("f58a94"))  # a glint


static func _cap(im: Image) -> void:
	# two floppy points, red to the left and blue to the right, each curling
	# out and down to a bell, with a darker fold along the underside
	_tri(im, Vector2(5, 12), Vector2(15, 12), Vector2(7, 1), RED)
	_tri(im, Vector2(5, 12), Vector2(9, 3), Vector2(1, 5), RED)
	_tri(im, Vector2(5, 12), Vector2(8, 12), Vector2(1.5, 6), RED_DARK)
	_tri(im, Vector2(15, 12), Vector2(25, 12), Vector2(23, 1), BLUE)
	_tri(im, Vector2(25, 12), Vector2(21, 3), Vector2(29, 5), BLUE)
	_tri(im, Vector2(22, 12), Vector2(25, 12), Vector2(28.5, 6), BLUE_DARK)
	# the band across his brow
	_rect(im, 4, 10, 22, 3, GOLD)
	_rect(im, 4, 12, 22, 1, GOLD_DARK)
	for x in [7, 11, 18, 22]:
		im.set_pixel(x, 11, GOLD_DARK)
	# bells at the tips
	for tip in [Vector2i(0, 5), Vector2i(27, 5)]:
		_rect(im, tip.x, tip.y, 3, 3, GOLD)
		im.set_pixel(tip.x + 2, tip.y + 2, GOLD_DARK)
		im.set_pixel(tip.x, tip.y, Color.WHITE)


static func _face(im: Image, eyes_open: bool, mouth: int) -> void:
	for ex in [10, 17]:
		if eyes_open:
			_rect(im, ex, 21, 3, 5, INK)
			im.set_pixel(ex, 21, Color.WHITE)
			im.set_pixel(ex, 22, Color.WHITE)
		else:
			_rect(im, ex, 24, 3, 1, INK)
	_rect(im, 7, 27, 2, 1, CHEEK)
	_rect(im, 21, 27, 2, 1, CHEEK)
	match mouth:
		0:  # a smile
			_rect(im, 13, 29, 4, 1, MOUTH)
			_px(im, [Vector2i(12, 28), Vector2i(17, 28)], MOUTH)
		1:
			_rect(im, 13, 28, 4, 2, MOUTH)
		_:
			_rect(im, 12, 28, 6, 3, MOUTH)
			_rect(im, 14, 30, 2, 1, TONGUE)


## A one-pixel dark edge round everything opaque.
static func _outline(im: Image) -> void:
	var edge := []
	for y in GH:
		for x in GW:
			if im.get_pixel(x, y).a > 0.0:
				continue
			for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
				var n: Vector2i = Vector2i(x, y) + d
				if n.x >= 0 and n.y >= 0 and n.x < GW and n.y < GH and im.get_pixel(n.x, n.y).a > 0.0:
					edge.append(Vector2i(x, y))
					break
	for p in edge:
		im.set_pixel(p.x, p.y, INK)
