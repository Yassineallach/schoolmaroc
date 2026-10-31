class_name Ads
extends Node

## AdMob for Aleatro through the AleatroAds Android plugin, with the rules
## from the monetisation plan: rewarded ads at three moments of need,
## interstitials only at real breaks (after a cash-out, when leaving a lost
## run), spaced by time and by rounds, never in the first run, and a quiet
## stretch after any rewarded ad. "Remove ads" (a one-time purchase) turns
## the interstitials off; rewarded ads stay available because players ask
## for them. Off Android every call quietly does nothing.

signal removed_changed(removed: bool)
signal privacy_changed(required: bool)
signal price_changed(price: String)
signal _finished(unit: String)

const CONFIG_PATH := "res://ads/ads.cfg"
const STATE_PATH := "user://ads_state.cfg"
## Google's sample units: they only ever serve test ads
const TEST_UNITS := {
	"interstitial": "ca-app-pub-3940256099942544/1033173712",
	"rewarded": "ca-app-pub-3940256099942544/5224354917",
}
## placement -> its format and its ad unit's key in ads.cfg
const SLOTS := {
	"cash_out": {"kind": "interstitial", "key": "interstitial_cash_out"},
	"run_end": {"kind": "interstitial", "key": "interstitial_run_end"},
	"second_chance": {"kind": "rewarded", "key": "rewarded_second_chance"},
	"shop_reroll": {"kind": "rewarded", "key": "rewarded_shop_reroll"},
	"pack_pick": {"kind": "rewarded", "key": "rewarded_pack_pick"},
}
## The plan's starting values (seconds, rounds, counts).
const RULES := {
	"min_gap": 300.0,  # since any full-screen ad
	"extra_gap_per_ad": 60.0,  # long sessions space out
	"min_rounds": 3,  # between cash-out interstitials
	"extra_rounds_per_ad": 1,
	"session_cap": 4,
	"daily_cap": 10,
	"quiet_after_rewarded": 600.0,  # a rewarded ad buys 10 quiet minutes
	"midrun_after_hours": 24.0,  # new players: run-end slot only at first
	"skip_stake_at": 8,  # Gold Chip runs stay clean
	"rewarded_daily_cap": 12,
	"session_gap": 1800.0,  # 30 minutes away starts a new session
	"remove_offer_every_days": 7.0,
	"remove_offer_after_ads": 5,
}
## How often each reward can be taken: per run, per shop, per ante.
const REWARD_LIMITS := {
	"second_chance": {"run": 1},
	"shop_reroll": {"run": 3, "shop": 1},
	"pack_pick": {"ante": 1},
}

var plugin: Object = null
var can_request := false  # consent allows ad requests
var started := false  # the Ads SDK is up
var privacy_required := false  # the player may change consent (Options shows it)
var removed := false  # bought "Remove ads"
var price := ""  # its localised price, once Play Billing answers
var remove_sku := "remove_ads"
var units := {}  # placement -> ad unit ID
var clock_offset := 0.0  # tests move time forward

var state := {}  # kept across launches: install time, today's counts, purchase
var session := {"inter": 0}
var last_fullscreen := -1.0e9
var last_rewarded := -1.0e9
var rounds_since_inter := 0
var uses := {"run": {}, "shop": {}, "ante": {}}
var _ante := -1
var _earned := {}
var _start_called := false
var _paused_at := -1.0


func _ready() -> void:
	_load_config()
	_load_state()
	if Engine.has_singleton("AleatroAds"):
		attach(Engine.get_singleton("AleatroAds"))


## Hook up a plugin (the real one, or a stand-in in tests).
func attach(p: Object) -> void:
	plugin = p
	plugin.consent_finished.connect(_on_consent)
	plugin.ads_ready.connect(_on_ready)
	plugin.ad_closed.connect(func(unit: String): _done(unit))
	plugin.ad_failed.connect(func(unit: String, msg: String):
		push_warning("Ad %s failed: %s" % [unit, msg])
		_done(unit))
	plugin.reward_earned.connect(func(unit: String): _earned[unit] = true)
	plugin.owned.connect(func(csv: String): _set_removed(remove_sku in csv.split(",")))
	plugin.price.connect(func(sku: String, p: String):
		if sku == remove_sku:
			price = p
			price_changed.emit(p))
	plugin.purchase_done.connect(func(sku: String):
		if sku == remove_sku:
			_set_removed(true))
	plugin.purchase_failed.connect(func(sku: String, msg: String): push_warning("Purchase %s failed: %s" % [sku, msg]))


## Ask for consent where needed and start the SDKs (once, after the splash).
func start() -> void:
	if plugin == null or _start_called:
		return
	_start_called = true
	plugin.start()
	plugin.start_billing(remove_sku)


func available() -> bool:
	return plugin != null


func now() -> float:
	return Time.get_ticks_msec() / 1000.0 + clock_offset


# ---------------------------------------------------------------- config

func _load_config() -> void:
	var cf := ConfigFile.new()
	var ok := cf.load(CONFIG_PATH) == OK
	# real units in every build (register your phone under AdMob > Test devices
	# to try them safely); test_ads=true switches to Google's sample units
	var test: bool = ok and cf.get_value("debug", "test_ads", false)
	for slot in SLOTS:
		var id: String = cf.get_value("units", SLOTS[slot].key, "") if ok else ""
		units[slot] = TEST_UNITS[SLOTS[slot].kind] if test or not id.contains("/") else id
	if ok:
		remove_sku = cf.get_value("iap", "remove_ads", remove_sku)


func _load_state() -> void:
	state = {"installed": Time.get_unix_time_from_system(), "day": "", "inter_today": 0, "rewarded_today": 0,
		"inter_total": 0, "removed": false, "last_offer": 0.0, "offered_first": false}
	var cf := ConfigFile.new()
	if cf.load(STATE_PATH) == OK:
		for k in state:
			state[k] = cf.get_value("ads", k, state[k])
	removed = state.removed
	_roll_day()


func _save_state() -> void:
	var cf := ConfigFile.new()
	for k in state:
		cf.set_value("ads", k, state[k])
	cf.save(STATE_PATH)


func _roll_day() -> void:
	var today := Time.get_date_string_from_system()
	if state.day != today:
		state.day = today
		state.inter_today = 0
		state.rewarded_today = 0
		_save_state()


func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_PAUSED:
		_paused_at = now()
	elif what == NOTIFICATION_APPLICATION_RESUMED and _paused_at >= 0.0:
		if now() - _paused_at > RULES.session_gap:
			session = {"inter": 0}
		_paused_at = -1.0


# ---------------------------------------------------------------- loading

func _on_consent(can: bool, privacy: bool) -> void:
	can_request = can
	privacy_required = privacy
	privacy_changed.emit(privacy)


func _on_ready() -> void:
	started = true
	for slot in SLOTS:
		_preload(slot)


func _preload(slot: String) -> void:
	if plugin == null or not started:
		return
	if SLOTS[slot].kind == "interstitial":
		if not removed:
			plugin.load_interstitial(units[slot])
	else:
		plugin.load_rewarded(units[slot])


func _loaded(slot: String) -> bool:
	return plugin != null and started and plugin.is_loaded(units[slot])


func _done(unit: String) -> void:
	# start fetching the next ad first: whoever waits on this one may want it
	for slot in SLOTS:
		if units[slot] == unit:
			_preload(slot)
	_finished.emit(unit)


# ---------------------------------------------------------------- run hooks

func on_run_start() -> void:
	uses.run = {}
	uses.shop = {}
	uses.ante = {}
	rounds_since_inter = 0


func on_round_end() -> void:
	rounds_since_inter += 1


func on_shop_open() -> void:
	uses.shop = {}


func _see_ante(ante: int) -> void:
	if ante != _ante:
		_ante = ante
		uses.ante = {}


# ---------------------------------------------------------------- interstitials

## Why an interstitial can't show now ("" when it can). `ctx`: runs_done,
## stake, challenge.
func interstitial_block(slot: String, ctx: Dictionary) -> String:
	_roll_day()
	if removed:
		return "removed"
	if int(ctx.get("runs_done", 0)) == 0:
		return "first_run"
	if slot == "cash_out" and (Time.get_unix_time_from_system() - float(state.installed)) / 3600.0 < RULES.midrun_after_hours:
		return "new_player"
	if String(ctx.get("challenge", "")) != "":
		return "challenge"
	if int(ctx.get("stake", 1)) >= RULES.skip_stake_at:
		return "stake"
	if state.inter_today >= RULES.daily_cap:
		return "daily_cap"
	if session.inter >= RULES.session_cap:
		return "session_cap"
	if now() - last_fullscreen < RULES.min_gap + RULES.extra_gap_per_ad * session.inter:
		return "too_soon"
	if now() - last_rewarded < RULES.quiet_after_rewarded:
		return "quiet_after_rewarded"
	if slot == "cash_out" and rounds_since_inter < RULES.min_rounds + RULES.extra_rounds_per_ad * session.inter:
		return "too_few_rounds"
	if not _loaded(slot):
		return "not_loaded"
	return ""


## Show an interstitial at `slot` if the rules allow; returns when it has
## closed (or at once). True if one was shown.
func maybe_interstitial(slot: String, ctx: Dictionary) -> bool:
	if interstitial_block(slot, ctx) != "":
		return false
	var unit: String = units[slot]
	plugin.show_interstitial(unit)
	await _wait_for(unit)
	last_fullscreen = now()
	rounds_since_inter = 0
	session.inter += 1
	state.inter_today += 1
	state.inter_total += 1
	_save_state()
	return true


# ---------------------------------------------------------------- rewarded

## Why reward `slot` can't be offered now ("" when it can). `ctx`: stake,
## challenge, ante.
func rewarded_block(slot: String, ctx: Dictionary) -> String:
	_roll_day()
	_see_ante(int(ctx.get("ante", 0)))
	if String(ctx.get("challenge", "")) != "":
		return "challenge"
	if int(ctx.get("stake", 1)) >= RULES.skip_stake_at:
		return "stake"
	if state.rewarded_today >= RULES.rewarded_daily_cap:
		return "daily_cap"
	var lim: Dictionary = REWARD_LIMITS.get(slot, {})
	for scope in lim:
		if int(uses[scope].get(slot, 0)) >= lim[scope]:
			return "used_" + scope
	if not _loaded(slot):
		return "not_loaded"
	return ""


func can_offer(slot: String, ctx: Dictionary) -> bool:
	return rewarded_block(slot, ctx) == ""


## Play reward `slot`'s ad; true once the player has earned the reward.
func show_rewarded(slot: String) -> bool:
	if not _loaded(slot):
		return false
	var unit: String = units[slot]
	_earned.erase(unit)
	plugin.show_rewarded(unit)
	await _wait_for(unit)
	var earned: bool = _earned.has(unit)
	_earned.erase(unit)
	if earned:
		last_rewarded = now()
		last_fullscreen = now()
		state.rewarded_today += 1
		_save_state()
		for scope in REWARD_LIMITS.get(slot, {}):
			uses[scope][slot] = int(uses[scope].get(slot, 0)) + 1
	return earned


func _wait_for(unit: String) -> void:
	while true:
		var u: String = await _finished
		if u == unit:
			return


# ---------------------------------------------------------------- remove ads

func buy_remove_ads() -> void:
	if plugin != null and not removed:
		plugin.purchase(remove_sku)


## Offer "Remove ads" once after the first finished run, then at most once a
## week after the fifth interstitial.
func should_offer_remove(runs_done: int) -> bool:
	if removed or plugin == null or price == "":
		return false
	if not state.offered_first and runs_done >= 1:
		return true
	var week: float = RULES.remove_offer_every_days * 86400.0
	return state.inter_total >= RULES.remove_offer_after_ads and Time.get_unix_time_from_system() - float(state.last_offer) > week


func mark_offered() -> void:
	state.offered_first = true
	state.last_offer = Time.get_unix_time_from_system()
	_save_state()


func show_privacy_options() -> void:
	if plugin != null:
		plugin.show_privacy_options()


func _set_removed(v: bool) -> void:
	if v == removed:
		return
	removed = v
	state.removed = v
	_save_state()
	removed_changed.emit(v)
