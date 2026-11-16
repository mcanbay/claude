extends Node
## Renders store screenshots by driving the real game. Run through tools/make_screenshots.sh.
## User args: --lang=tr|en --out=<absolute dir>

var _out := ""
var _main: Node
var _game: Game
var _ui: UIRoot


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	var lang := "tr"
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--lang="):
			lang = a.get_slice("=", 1)
		elif a.begins_with("--out="):
			_out = a.get_slice("=", 1)
	Settings.file_path = "user://shot_settings.json"
	SaveData.file_path = "user://shot_save.json"
	SaveData.saved_run = {}
	SaveData.best_score = 2480
	Settings.tutorial_seen = true
	Settings.sfx_on = false
	Settings.music_on = false
	Settings.set_language(lang)
	_main = (load("res://src/main.tscn") as PackedScene).instantiate()
	add_child(_main)
	_game = _main.game
	_ui = _main.ui
	await _wait(20)
	await _shot("01_menu")

	_ui._start_new()
	_game._score.score = 1836
	_game.score_changed.emit(1836)
	var rng := RandomNumberGenerator.new()
	rng.seed = 4
	var layout := [[9, 150, 760], [8, 420, 780], [6, 570, 800], [7, 300, 560], [5, 520, 620], [4, 110, 560],
			[6, 450, 470], [3, 200, 430], [2, 330, 400], [5, 590, 480], [1, 80, 470], [4, 260, 330], [3, 520, 350],
			[1, 400, 320], [2, 140, 380]]
	for item: Array in layout:
		_game.debug_add_fruit(item[0], Vector2(item[1], item[2]))
	await _wait(150)
	_game.aim(250.0)
	await _wait(5)
	await _shot("02_gameplay")

	# A merge in progress: drop a fruit next to its twin.
	var target: Fruit = null
	for f: Fruit in _game.board.fruits_root.get_children():
		if not f.held and f.tier == _game.held_tier() and (target == null or f.position.y < target.position.y):
			target = f
	if target != null:
		_game.aim(target.position.x + 6.0)
	_game.drop()
	for i in 120:
		await get_tree().physics_frame
		if _game.effects.get_child_count() > 0:
			break
	await _wait(9)
	await _shot("03_fusion")

	await _wait(60)
	_game.pause()
	_ui._open_tutorial(Callable())
	_ui._close(_ui._pause)
	await _wait(20)
	await _shot("04_how_to_play")
	_ui._close(_ui._tutorial)
	_ui._open(_ui._pause)
	_ui._open(_ui._settings)
	await _wait(20)
	await _shot("05_settings")
	_ui._close(_ui._settings)
	_game.resume()

	_ui._restart()
	_game._score.score = 2764
	_game.score_changed.emit(2764)
	var y := Board.H
	for t: int in [10, 9, 8, 7]:
		y -= FruitCatalog.radius(t)
		_game.debug_add_fruit(t, Vector2(330, y))
		y -= FruitCatalog.radius(t)
	for item: Array in [[6, 82, 818], [5, 572, 832], [4, 60, 680], [3, 590, 720], [2, 45, 590], [1, 610, 650]]:
		_game.debug_add_fruit(item[0], Vector2(item[1], item[2]))
	for i in 400:
		await get_tree().physics_frame
		if _game.state == Game.State.GAME_OVER:
			break
	await _wait(70)
	await _shot("06_game_over")
	get_tree().quit()


func _wait(frames: int) -> void:
	for i in frames:
		await get_tree().process_frame


func _shot(shot_name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGB8)
	img.save_png(_out.path_join(shot_name + ".png"))
	print("saved ", shot_name, " ", img.get_size())
