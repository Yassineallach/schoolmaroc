class_name PileView
extends Control

## The draw pile (a stack of card backs) or the discard pile (a messy heap
## of the last cards thrown on it).

signal tapped

const W := 80.0
const H := 112.0

var discard := false
var count := 0
var total := 0
var _heap: Array = []  # [card, rotation, offset] for the discard pile
var _shuffle := 0.0


func _init(is_discard := false) -> void:
	discard = is_discard
	size = Vector2(W, H + 26)
	pivot_offset = Vector2(W, H) / 2
	mouse_filter = Control.MOUSE_FILTER_STOP


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		tapped.emit()
		accept_event()


func set_count(n: int, of: int) -> void:
	count = n
	total = of
	queue_redraw()


func add(card: Dictionary) -> void:
	_heap.append([card, randf_range(-0.35, 0.35), Vector2(randf_range(-8, 8), randf_range(-6, 6))])
	if _heap.size() > 7:
		_heap.pop_front()
	queue_redraw()


func clear() -> void:
	_heap.clear()
	queue_redraw()


## Cards riffle back and forth for a moment.
func shuffle() -> void:
	var tw := create_tween()
	tw.tween_method(func(v):
		_shuffle = sin(v * TAU * 4.0) * (1.0 - v)
		queue_redraw(), 0.0, 1.0, 0.7)


## Where a card flying to or from this pile should aim (global, card-sized).
func card_target() -> Vector2:
	return global_position + Vector2(W, H) / 2 - Vector2(CardView.W, CardView.H) / 2


func _draw() -> void:
	var font := ThemeDB.fallback_font
	var slot := PixelBox.new(Color(0, 0, 0, 0.22), 4.0)
	slot.rounded = true
	slot.outline = 2.0
	slot.outline_color = Color(1, 1, 1, 0.12)
	draw_style_box(slot, Rect2(Vector2.ZERO, Vector2(W, H)))
	var sc := W / CardView.W
	if discard:
		for h in _heap:
			draw_set_transform(Vector2(W, H) / 2 + h[2], h[1], Vector2(sc, sc) * 0.95)
			_draw_mini_face(h[0])
		draw_set_transform(Vector2.ZERO, 0, Vector2.ONE)
	else:
		var layers := mini(ceili(count / 6.0), 9)
		for i in layers:
			var jitter := _shuffle * (12.0 if i % 2 else -12.0)
			var off := Vector2(-i * 1.2 + jitter, -i * 1.6)
			var back := PixelBox.new(CardView.back_color if i < layers - 1 else CardView.back_color.lightened(0.06), 4.0, 0.0, i == 0)
			back.rounded = true
			back.outline = 2.0
			back.outline_color = Color(1, 1, 1, 0.35)
			if CardView.back_art != null:
				# every card in the stack shows the deck's back; the ones below are shaded
				back.color = Color(0, 0, 0, 0)
				back.outline = 0.0
				draw_style_box(back, Rect2(off + Vector2(2, 2), Vector2(W - 4, H - 4)))
				var shade := Color.WHITE if i == layers - 1 else Color(0.6, 0.6, 0.6)
				draw_texture_rect(CardView.back_art, Rect2(off + Vector2(2, 2), Vector2(W - 4, H - 4)), false, shade)
			else:
				draw_style_box(back, Rect2(off + Vector2(2, 2), Vector2(W - 4, H - 4)))
		if layers > 0 and CardView.back_art == null:
			var top := Vector2(-(layers - 1) * 1.2, -(layers - 1) * 1.6)
			draw_string(font, top + Vector2(0, H / 2 + 8), "A", HORIZONTAL_ALIGNMENT_CENTER, W, 28, Color(1, 1, 1, 0.5))
	var label := ("%d/%d" % [count, total]) if not discard else "Discard"
	draw_string(font, Vector2(0, H + 21), label, HORIZONTAL_ALIGNMENT_CENTER, W, 18, Color(1, 1, 1, 0.75))


func _draw_mini_face(card: Dictionary) -> void:
	var r := Rect2(-Vector2(CardView.W, CardView.H) / 2, Vector2(CardView.W, CardView.H))
	var enh: String = card.get("enh", "")
	var face := PixelBox.new(Data.ENHANCEMENTS[enh].face if enh != "" else Color("f7f3ea"), 4.0, 0.0, true)
	face.rounded = true
	face.outline = 2.0
	face.outline_color = Color("c9c2b0")
	var art := CardView.enh_face(enh)
	if art != null:
		face.color = Color(0, 0, 0, 0)
		face.outline = 0.0
	draw_style_box(face, r)
	if art != null:
		draw_texture_rect(art, r, false)
	var col: Color = Data.SUIT_COLORS[card.suit]
	draw_string(ThemeDB.fallback_font, r.position + Vector2(8, 30), Data.RANK_LABELS[card.rank], HORIZONTAL_ALIGNMENT_LEFT, -1, 26, col)
	CardView.draw_suit(self, card.suit, Vector2.ZERO, 40.0, col)
