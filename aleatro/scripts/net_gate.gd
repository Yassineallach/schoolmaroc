class_name NetGate
extends CanvasLayer

## Aleatro needs an internet connection to be played. The gate checks for one
## at launch, every so often while playing and whenever the app comes back to
## the front. Without one it covers the screen with a "No internet
## connection" card and pauses the game (its timers, animations and input)
## until a check succeeds again. The run in progress is kept.
##
## A check is a tiny HTTPS request to a "generate_204" address (what Android
## itself uses to detect a connection); a Wi-Fi login page that answers with
## something else counts as offline.
##
## On by default only on Android. ALEATRO_NET_GATE=1 turns it on elsewhere
## (to try it on a computer), ALEATRO_NET_GATE=0 turns it off.

signal changed(online: bool)

const PROBES := [
	{"url": "https://connectivitycheck.gstatic.com/generate_204", "code": 204},
	{"url": "https://www.google.com/generate_204", "code": 204},
	{"url": "https://cp.cloudflare.com/generate_204", "code": 204},
]
const CHECK_EVERY := 30.0  # seconds between checks while online
const RETRY_EVERY := 4.0  # and while blocked
const TIMEOUT := 6.0
## In play, a single failed check could be a moment in a tunnel: block only
## after this many in a row. The first check at launch blocks at once.
const FAILS_TO_BLOCK := 2

var enabled := false
var online := true
var checked := false  # a check has finished at least once
var _fails := 0
var _wait := 0.0
var _probe := -1  # index into PROBES while a check runs; -1 when idle
var _http: HTTPRequest
var _main: Node  # Main, for its label and button builders
var _cover: Control
var _status: Label
var _retry: Button


func _init(main: Node) -> void:
	_main = main
	layer = 120  # over the splash (100) and every modal, under the CRT pass (128)
	process_mode = Node.PROCESS_MODE_ALWAYS  # keeps working while the game is paused
	var env := OS.get_environment("ALEATRO_NET_GATE")
	enabled = env == "1" or (env != "0" and OS.has_feature("android"))


func _ready() -> void:
	_http = HTTPRequest.new()
	_http.timeout = TIMEOUT
	_http.use_threads = true
	_http.request_completed.connect(_on_probe_done)
	add_child(_http)
	_build_cover()
	if enabled:
		check_now()


func _process(delta: float) -> void:
	if not enabled or _probe >= 0:
		return
	_wait -= delta
	if _wait <= 0.0:
		check_now()


func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_RESUMED and enabled and _probe < 0:
		check_now()


## Start a check now (unless one is running).
func check_now() -> void:
	if _probe >= 0:
		return
	_set_status(tr("Checking connection…") if not online else "")
	_start_probe(0)


func _start_probe(i: int) -> void:
	_probe = i
	_http.cancel_request()
	if _http.request(PROBES[i].url, PackedStringArray(["Cache-Control: no-cache"])) != OK:
		_on_probe_done(HTTPRequest.RESULT_CANT_CONNECT, 0, PackedStringArray(), PackedByteArray())


func _on_probe_done(result: int, code: int, _headers: PackedStringArray, _body: PackedByteArray) -> void:
	if _probe < 0:
		return
	var ok: bool = result == HTTPRequest.RESULT_SUCCESS and code == int(PROBES[_probe].code)
	if not ok and _probe + 1 < PROBES.size():
		_start_probe(_probe + 1)  # try the next address before calling it offline
		return
	_probe = -1
	report(ok)


## Record the outcome of one check (tests call this directly).
func report(ok: bool) -> void:
	var first := not checked
	checked = true
	if ok:
		_fails = 0
		_set_online(true)
	else:
		_fails += 1
		if first or _fails >= FAILS_TO_BLOCK or not online:
			_set_online(false)
	_wait = CHECK_EVERY if online else RETRY_EVERY
	_set_status(tr("Retrying in a moment…") if not online else "")


func _set_online(v: bool) -> void:
	_cover.visible = not v
	get_tree().paused = not v
	if v == online:
		return
	online = v
	changed.emit(v)


# ---------------------------------------------------------------- the card

func _build_cover() -> void:
	_cover = Control.new()
	_cover.set_anchors_preset(Control.PRESET_FULL_RECT)
	_cover.mouse_filter = Control.MOUSE_FILTER_STOP  # nothing behind it can be touched
	_cover.visible = false
	_cover.theme = _main.theme  # the game's font and sizes (a CanvasLayer doesn't inherit them)
	add_child(_cover)
	var dim := ColorRect.new()
	dim.color = Color(Palette.TABLE_DARK, 0.92)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_cover.add_child(dim)
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	_cover.add_child(center)
	var panel := PanelContainer.new()
	var sb := PixelBox.new(Palette.PANEL, 4.0, 0.0, true)
	sb.content_margin_left = 40
	sb.content_margin_right = 40
	sb.content_margin_top = 28
	sb.content_margin_bottom = 28
	sb.outline_color = Palette.ROSE
	panel.add_theme_stylebox_override("panel", sb)
	center.add_child(panel)
	var vb := VBoxContainer.new()
	vb.add_theme_constant_override("separation", 18)
	panel.add_child(vb)
	vb.add_child(_main._label("No internet connection", 40, Palette.HEADING))
	var body: Label = _main._label("Aleatro needs an internet connection to play. Turn on Wi-Fi or mobile data, then tap Retry.", 22, Palette.TEXT_SUB)
	body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	body.custom_minimum_size = Vector2(700, 0)
	vb.add_child(body)
	_status = _main._label("", 18, Color(1, 1, 1, 0.55))
	vb.add_child(_status)
	_retry = _main._button("Retry", Palette.TEAL, check_now, Vector2(220, 70), 26)
	var row := CenterContainer.new()
	row.add_child(_retry)
	vb.add_child(row)


func _set_status(text: String) -> void:
	if _status != null:
		_status.text = text
