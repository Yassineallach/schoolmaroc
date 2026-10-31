extends SceneTree
## Usage (from the project folder):
##   LANG_SHOT=de STORE_OUT=/abs/out/dir xvfb-run -a -s "-screen 0 2600x1500x24" \
##     godot --rendering-driver opengl3 --resolution 2560x1440 -s tools/store/capture.gd
## Raw store screenshots, one language per run (LANG_SHOT), at the window size.
var OUT := OS.get_environment("STORE_OUT").path_join("")
var main
var lang: String
var score_times := []
func _initialize():
	lang = OS.get_environment("LANG_SHOT")
	var st := OS.get_environment("SCORE_TIMES")
	score_times = Array(st.split(",")).map(func(s): return float(s)) if st != "" else [3.6, 3.8, 4.0]
	main = load("res://scenes/main.tscn").instantiate()
	root.add_child(main)
	run()
func shot(n):
	await process_frame; await process_frame; await process_frame
	root.get_texture().get_image().save_png(OUT + lang + "_" + n + ".png")
func run():
	await create_timer(0.4).timeout
	root.warp_mouse(Vector2(-50, -50))
	main.set_language(lang)
	var p = main.profile_data
	p.tips_off = true
	p.unlocked = Unlocks.GOALS.keys()
	p.seen_charms = Data.CHARMS.map(func(c): return c.id)
	main.show_title(); await create_timer(1.2).timeout
	await shot("title")
	main.new_run(""); await create_timer(0.3).timeout
	var gs = main.gs
	gs.charms = [{"id": "jester", "data": {}, "ed": "foil"}, {"id": "hologram", "data": {"x": 2.5}, "ed": ""},
		{"id": "bonfire", "data": {}, "ed": "chroma"}, {"id": "regent", "data": {}, "ed": "holo"}, {"id": "mimic", "data": {}, "ed": "negative"}]
	gs.spells = ["soul", "rune:Flush"]
	main.rebuild_charms(); main.rebuild_spells()
	gs.tags = ["riches", "dice", "chroma"]; main.show_blind_select(); await create_timer(0.8).timeout
	await shot("blind")
	main.start_blind(); await create_timer(1.8).timeout
	var vs: Array = main.hand_views
	var plan := [[14, 1, "foil", "golden"], [13, 1, "", ""], [12, 1, "", ""], [10, 1, "holo", ""], [9, 1, "", ""]]
	for i in plan.size():
		var c: Dictionary = vs[i].card
		c.rank = plan[i][0]; c.suit = plan[i][1]; c.ed = plan[i][2]; c.seal = plan[i][3]
		vs[i].queue_redraw()
	main.sort_hand(); await create_timer(0.6).timeout
	for v in vs.duplicate():
		if v.card.suit == 1 and v.card.rank in [14, 13, 12, 10, 9] and main.selected_views().size() < 5:
			main._on_card_tapped(v)
	await create_timer(0.5).timeout
	await shot("hand")
	main.play_selected()
	var t0 := 0.0
	for i in score_times.size():
		await create_timer(score_times[i] - t0).timeout
		t0 = score_times[i]
		await shot("score%d" % i)
	await create_timer(6.0).timeout
	gs.tags = []
	gs.money = 60
	main.open_shop(); await create_timer(0.4).timeout
	gs.shop_items = [{"type": "charm", "id": "moonshot", "base": 6, "ed": "foil"}, {"type": "charm", "id": "juggler", "base": 6}]
	gs.shop_packs = [{"id": "arcana_jumbo"}, {"id": "spectral"}]; gs.shop_vouchers = ["nestbox"]
	main.show_shop(); await create_timer(1.2).timeout
	await shot("shop")
	gs.money = 60
	gs.shop_packs[0] = {"id": "celestial_mega"}
	main.buy_pack(0); await create_timer(1.6).timeout
	await shot("pack")
	main.show_title(); await create_timer(1.5).timeout
	main.show_collection("charms", 0); await create_timer(0.8).timeout
	await shot("coll")
	main.close_modal()
	main.show_run_setup(); await create_timer(0.8).timeout
	await shot("setup")
	quit()
