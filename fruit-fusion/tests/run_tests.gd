extends Node
## Headless test runner.
##   godot --headless --fixed-fps 60 --path . res://tests/run_tests.tscn
## Exit code 0 = all passed. Uses separate save files so real player data is never touched.

var _fails := 0
var _checks := 0
var _current := ""
var _game: Game


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	Settings.file_path = "user://test_settings.json"
	SaveData.file_path = "user://test_save.json"
	_wipe()
	var names: Array[String] = []
	for m in get_method_list():
		if str(m.name).begins_with("test_"):
			names.append(m.name)
	names.sort()
	var failed_tests := 0
	for n in names:
		_current = n
		var before := _fails
		_wipe()
		await call(n)
		if _game != null:
			get_tree().paused = false
			_game.queue_free()
			_game = null
			await get_tree().physics_frame
		print("%s  %s" % ["PASS" if _fails == before else "FAIL", n])
		if _fails != before:
			failed_tests += 1
	_wipe()
	print("\n%d tests, %d failed, %d checks" % [names.size(), failed_tests, _checks])
	get_tree().quit(1 if _fails > 0 else 0)


func _wipe() -> void:
	for p in [Settings.file_path, SaveData.file_path]:
		if FileAccess.file_exists(p):
			DirAccess.remove_absolute(p)
	SaveData.load_data()
	Settings.sfx_on = true
	Settings.music_on = true
	Settings.haptics_on = true
	Settings.tutorial_seen = false
	Settings.language = "tr"
	TranslationServer.set_locale("tr")


func ok(cond: bool, msg: String) -> void:
	_checks += 1
	if not cond:
		_fails += 1
		printerr("    ✗ %s: %s" % [_current, msg])


func eq(got: Variant, want: Variant, msg: String) -> void:
	ok(got == want, "%s (got %s, want %s)" % [msg, got, want])


func _new_game(rng_seed: int = 7) -> Game:
	_game = Game.new()
	add_child(_game)
	_game.set_layout(Rect2(0, 0, Board.W + 16.0, Board.H + 8.0))
	_game.start_new_game(rng_seed)
	return _game


func _step(frames: int) -> void:
	for i in frames:
		await get_tree().physics_frame


func _floor_y(tier: int) -> float:
	return Board.H - FruitCatalog.radius(tier)


# ------------------------------------------------------------ fruit progression

func test_progression_catalog() -> void:
	eq(FruitCatalog.MAX_TIER, 11, "11 tiers")
	eq(FruitCatalog.RADII.size(), 11, "radius per tier")
	eq(FruitCatalog.COLORS.size(), 11, "colour per tier")
	for t in range(1, 11):
		eq(FruitCatalog.next_tier(t), t + 1, "tier %d merges into %d" % [t, t + 1])
		ok(FruitCatalog.radius(t + 1) > FruitCatalog.radius(t), "radius grows at tier %d" % t)
	eq(FruitCatalog.next_tier(11), 0, "top tier bursts")
	ok(not FruitCatalog.is_valid(0) and not FruitCatalog.is_valid(12), "invalid tiers rejected")
	ok(FruitCatalog.radius(11) * 2.0 < Board.W, "largest fruit fits the jar")
	ok(Board.DROP_Y + FruitCatalog.radius(FruitCatalog.max_drop_tier()) < Board.DANGER_Y, "held fruit sits above danger line")


func test_progression_drop_queue() -> void:
	var a := DropQueue.new(42)
	var b := DropQueue.new(42)
	var seen := {}
	for i in 500:
		eq(a.peek(), b.peek(), "peek deterministic")
		var t := a.pop()
		eq(t, b.pop(), "same seed same sequence")
		ok(t >= 1 and t <= FruitCatalog.max_drop_tier(), "droppable tier in range")
		seen[t] = true
	eq(seen.size(), FruitCatalog.max_drop_tier(), "all droppable tiers appear")
	var restored := DropQueue.from_dict(JSON.parse_string(JSON.stringify(a.to_dict())))
	for i in 50:
		eq(restored.pop(), a.pop(), "sequence continues after JSON round trip")


# ------------------------------------------------------------ score

func test_score_calculation() -> void:
	eq(ScoreSystem.points_for_created(2), 3, "tier 2 worth 3")
	eq(ScoreSystem.points_for_created(11), 66, "tier 11 worth 66")
	eq(ScoreSystem.base_points_for_merge(1), 3, "merging tier 1")
	eq(ScoreSystem.base_points_for_merge(11), ScoreSystem.FUSION_BONUS, "fusion burst bonus")
	eq(ScoreSystem.multiplier(1), 1.0, "no combo")
	eq(ScoreSystem.multiplier(2), 1.5, "combo 2")
	eq(ScoreSystem.multiplier(50), 3.0, "combo cap")
	var s := ScoreSystem.new()
	eq(s.register_merge(1), 3, "first merge")
	eq(s.register_merge(2), 9, "second merge in window ×1.5")
	eq(s.score, 12, "score accumulates")
	s.tick(0.5)
	eq(s.combo, 2, "combo alive inside window")
	s.tick(0.6)
	eq(s.combo, 0, "combo expires")
	eq(s.register_merge(1), 3, "multiplier resets")
	s.reset()
	eq(s.score, 0, "reset clears score")


# ------------------------------------------------------------ duplicate merge prevention

func test_merge_resolver_no_duplicates() -> void:
	var pairs: Array = [Vector3i(1, 2, 1), Vector3i(2, 1, 1), Vector3i(2, 3, 1), Vector3i(3, 4, 1),
			Vector3i(5, 6, 4), Vector3i(6, 7, 4), Vector3i(8, 8, 2)]
	var want: Array[Vector3i] = [Vector3i(5, 6, 4), Vector3i(1, 2, 1), Vector3i(3, 4, 1)]
	eq(MergeResolver.resolve(pairs), want, "expected merges")
	var rng := RandomNumberGenerator.new()
	rng.seed = 3
	for i in 30:
		var shuffled := pairs.duplicate()
		for j in range(shuffled.size() - 1, 0, -1):
			var k := rng.randi_range(0, j)
			var tmp: Vector3i = shuffled[j]
			shuffled[j] = shuffled[k]
			shuffled[k] = tmp
		eq(MergeResolver.resolve(shuffled), want, "order independent")
	var used := {}
	for m in MergeResolver.resolve(pairs):
		ok(not used.has(m.x) and not used.has(m.y), "uid used once")
		used[m.x] = true
		used[m.y] = true
	eq(MergeResolver.resolve([]).size(), 0, "empty input")


func test_physics_single_merge() -> void:
	var g := await _new_game()
	var hits := [0]
	g.merged.connect(func(_t: int, _p: int, _c: int, _pos: Vector2) -> void: hits[0] += 1)
	var r := FruitCatalog.radius(1)
	g.debug_add_fruit(1, Vector2(300, _floor_y(1)))
	g.debug_add_fruit(1, Vector2(300 + r * 2 - 2, _floor_y(1)))
	await _step(30)
	eq(g.fruit_tiers(), [2] as Array[int], "two blueberries become one sour cherry")
	eq(hits[0], 1, "merged signal exactly once")
	eq(g.score, 3, "score for one merge")


func test_physics_triple_contact_merges_once() -> void:
	var g := await _new_game()
	var r := FruitCatalog.radius(3)
	for i in 3:
		g.debug_add_fruit(3, Vector2(200 + i * (r * 2 - 2), _floor_y(3)))
	await _step(40)
	eq(g.fruit_tiers(), [3, 4] as Array[int], "three in contact: one merge, one left over")
	eq(g.score, 10, "only one merge scored")


func test_physics_chain_reaction() -> void:
	var g := await _new_game()
	var r1 := FruitCatalog.radius(1)
	var r2 := FruitCatalog.radius(2)
	g.debug_add_fruit(1, Vector2(300, _floor_y(1)))
	g.debug_add_fruit(1, Vector2(300 + r1 * 2 - 2, _floor_y(1)))
	g.debug_add_fruit(2, Vector2(300 + r1 - 1, _floor_y(1) - sqrt((r1 + r2) ** 2 - r1 ** 2) + 1))
	await _step(50)
	eq(g.fruit_tiers(), [3] as Array[int], "chain 1+1→2, 2+2→3")
	eq(g.score, 3 + 9, "chain combo multiplier applied")


func test_physics_fusion_burst() -> void:
	var g := await _new_game()
	var r := FruitCatalog.radius(11)
	g.debug_add_fruit(11, Vector2(320, _floor_y(11)))
	g.debug_add_fruit(11, Vector2(320, _floor_y(11) - r * 2 + 2))
	await _step(20)
	eq(g.fruit_count(), 0, "two top-tier fruits vanish")
	eq(g.score, ScoreSystem.FUSION_BONUS, "fusion bonus")


func test_physics_fruits_stay_in_jar() -> void:
	var g := await _new_game(11)
	var rng := RandomNumberGenerator.new()
	rng.seed = 5
	for i in 40:
		g.aim(rng.randf_range(0.0, Board.W))
		g.drop()
		await _step(34)
		if g.state != Game.State.PLAYING:
			break
	await _step(120)
	for f: Fruit in g.board.fruits_root.get_children():
		if f.held or f.consumed:
			continue
		ok(f.position.x > 0.0 and f.position.x < Board.W and f.position.y < Board.H + 1.0,
				"fruit %d inside jar at %s" % [f.uid, f.position])
	ok(g.score > 0, "random play produced merges")


# ------------------------------------------------------------ dropping

func test_drop_and_cooldown() -> void:
	var g := await _new_game()
	var first := g.held_tier()
	ok(first >= 1, "a fruit is held at start")
	g.aim(-500.0)
	ok(g.drop(), "drop succeeds")
	eq(g.fruit_count(), 1, "dropped fruit is live")
	ok(not g.drop(), "cannot drop during cooldown")
	eq(g.held_tier(), 0, "nothing held during cooldown")
	await _step(40)
	ok(g.held_tier() >= 1, "next fruit appears after cooldown")
	var f: Fruit = g.board.fruits_root.get_child(0)
	ok(f.position.x >= f.radius, "aim clamped inside the jar")


# ------------------------------------------------------------ game over / restart

func _build_overflow(g: Game) -> void:
	var y := Board.H
	for t in [10, 9, 8, 7]:
		var r := FruitCatalog.radius(t)
		y -= r
		g.debug_add_fruit(t, Vector2(320, y))
		y -= r


func test_danger_monitor() -> void:
	var d := DangerMonitor.new()
	ok(not d.update(1.0, true), "not yet")
	ok(not d.update(1.0, true), "still not")
	ok(not d.update(0.1, false), "reset when clear")
	eq(d.ratio(), 0.0, "ratio back to zero")
	ok(not d.update(2.4, true), "just under limit")
	ok(d.update(0.2, true), "fires at limit")


func test_game_over_and_restart() -> void:
	var g := await _new_game()
	var overs: Array = []
	g.game_over.connect(func(s: int, best: bool) -> void: overs.append([s, best]))
	g.debug_add_fruit(1, Vector2(100, _floor_y(1)))
	g.debug_add_fruit(1, Vector2(100 + 46, _floor_y(1)))
	_build_overflow(g)
	await _step(60)
	eq(g.state, Game.State.PLAYING, "not over before the limit")
	await _step(140)
	eq(g.state, Game.State.GAME_OVER, "game over after fruit stays above the line")
	eq(overs.size(), 1, "game_over emitted once")
	eq(overs[0], [3, true], "final score and new best")
	eq(SaveData.best_score, 3, "best score stored")
	ok(not SaveData.has_run(), "no resumable run after game over")
	ok(not g.drop(), "no dropping after game over")
	await _step(30)
	eq(overs.size(), 1, "game_over not repeated")
	g.start_new_game(9)
	await _step(2)
	eq(g.state, Game.State.PLAYING, "restart is immediate")
	eq(g.score, 0, "score reset")
	eq(g.fruit_count(), 0, "board cleared")
	ok(g.held_tier() >= 1, "new fruit ready")
	eq(g.board.fruits_root.get_child_count(), 1, "only the held fruit exists")
	await _step(200)
	eq(g.state, Game.State.PLAYING, "danger timer was reset")
	eq(SaveData.best_score, 3, "best kept across restart")


func test_falling_fruit_does_not_trigger_danger() -> void:
	var g := await _new_game()
	for i in 6:
		g.aim(60.0 + i * 100.0)
		g.drop()
		await _step(40)
	eq(g.state, Game.State.PLAYING, "dropping through the danger zone is safe")


# ------------------------------------------------------------ save / load

func test_save_load_best_and_settings() -> void:
	ok(SaveData.submit_score(120), "first score is best")
	ok(not SaveData.submit_score(80), "lower score is not best")
	SaveData.best_score = 0
	SaveData.load_data()
	eq(SaveData.best_score, 120, "best score persisted")
	Settings.set_music(false)
	Settings.set_haptics(false)
	Settings.set_language("en")
	Settings.set_tutorial_seen(true)
	Settings.music_on = true
	Settings.haptics_on = true
	Settings.language = "tr"
	Settings.tutorial_seen = false
	Settings.load_settings()
	ok(not Settings.music_on and not Settings.haptics_on, "toggles persisted")
	ok(Settings.sfx_on, "sfx independent of music")
	eq(Settings.language, "en", "language persisted")
	ok(Settings.tutorial_seen, "tutorial flag persisted")


func test_save_load_corrupt_file() -> void:
	var f := FileAccess.open(SaveData.file_path, FileAccess.WRITE)
	f.store_string("{not json")
	f.close()
	SaveData.load_data()
	eq(SaveData.best_score, 0, "corrupt save falls back to defaults")
	ok(not SaveData.has_run(), "no run from corrupt save")
	SaveData.save_run({"v": 99, "fruits": "nope"})
	var g := Game.new()
	_game = g
	add_child(g)
	ok(not g.resume_saved_game(), "invalid run rejected")
	ok(not SaveData.has_run(), "invalid run discarded")


func test_save_load_run_round_trip() -> void:
	var g := await _new_game(21)
	g.debug_add_fruit(4, Vector2(120, _floor_y(4)))
	g.debug_add_fruit(6, Vector2(320, _floor_y(6)))
	g.debug_add_fruit(2, Vector2(520, _floor_y(2)))
	g.debug_add_fruit(2, Vector2(520 + 64, _floor_y(2)))
	await _step(40)
	var tiers := g.fruit_tiers()
	var held := g.held_tier()
	eq(tiers, [3, 4, 6] as Array[int], "setup merged as expected")
	g.pause()
	eq(g.state, Game.State.PAUSED, "paused")
	ok(get_tree().paused, "tree paused")
	ok(SaveData.has_run(), "run saved on pause")
	await _step(30)
	eq(g.fruit_tiers(), tiers, "nothing moves while paused")
	g.resume()
	eq(g.state, Game.State.PLAYING, "resumed")
	g.quit_to_menu()
	eq(g.state, Game.State.IDLE, "idle in menu")
	eq(g.fruit_count(), 0, "board cleared in menu")
	# Simulate an app relaunch: reload from disk into a brand new Game.
	g.queue_free()
	SaveData.saved_run = {}
	SaveData.load_data()
	ok(SaveData.has_run(), "run survives reload from disk")
	var g2 := Game.new()
	_game = g2
	add_child(g2)
	g2.set_layout(Rect2(0, 0, Board.W + 16.0, Board.H + 8.0))
	ok(g2.resume_saved_game(), "run restored")
	eq(g2.fruit_tiers(), tiers, "same fruits")
	eq(g2.score, 6, "same score")
	eq(g2.held_tier(), held, "same held fruit")
	await _step(60)
	eq(g2.fruit_tiers(), tiers, "restored pile is stable")


# ------------------------------------------------------------ localization

func test_localization_csv_complete() -> void:
	var f := FileAccess.open("res://localization/strings.csv", FileAccess.READ)
	ok(f != null, "strings.csv readable")
	var header := f.get_csv_line()
	eq(Array(header), ["keys", "en", "tr"], "csv header")
	var keys := {}
	while not f.eof_reached():
		var row := f.get_csv_line()
		if row.size() == 1 and row[0] == "":
			continue
		eq(row.size(), 3, "3 columns for %s" % row[0])
		if row.size() < 3:
			continue
		ok(not keys.has(row[0]), "duplicate key %s" % row[0])
		keys[row[0]] = true
		ok(row[1].strip_edges() != "", "en text for %s" % row[0])
		ok(row[2].strip_edges() != "", "tr text for %s" % row[0])
	ok(keys.size() >= 11, "keys present")
	for src in ["res://src/ui", "res://src/game"]:
		for file in DirAccess.get_files_at(src):
			if not file.ends_with(".gd"):
				continue
			var text := FileAccess.get_file_as_string(src + "/" + file)
			var re := RegEx.create_from_string("\"((?:UI|FRUIT)_[A-Z0-9_]+)\"")
			for m in re.search_all(text):
				ok(keys.has(m.get_string(1)), "key %s used in %s exists" % [m.get_string(1), file])


func test_localization_loading_and_switch() -> void:
	var locales := TranslationServer.get_loaded_locales()
	ok("tr" in locales and "en" in locales, "tr and en translations loaded")
	Settings.set_language("tr")
	eq(tr("FRUIT_2"), "Vişne", "Turkish with proper characters")
	eq(tr("FRUIT_7"), "Şeftali", "Turkish Ş")
	Settings.set_language("en")
	eq(tr("FRUIT_2"), "Sour cherry", "English")
	Settings.set_language("xx")
	eq(Settings.language, "en", "unknown language ignored")
	for t in range(1, FruitCatalog.MAX_TIER + 1):
		for lang in ["tr", "en"]:
			TranslationServer.set_locale(lang)
			ok(tr(FruitCatalog.name_key(t)) != FruitCatalog.name_key(t), "fruit %d named in %s" % [t, lang])
