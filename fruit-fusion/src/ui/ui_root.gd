class_name UIRoot
extends CanvasLayer
## All screens: main menu, HUD, pause, settings, tutorial, game over.
## Text properties hold translation keys; Godot re-translates them live when the locale changes.

const BTN_SIZE := Vector2(520, 100)
const HUD_H := 200.0

var game: Game

var _root: Control
var _hud: Control
var _menu: Control
var _pause: Control
var _settings: Control
var _tutorial: Control
var _over: Control

var _score_value: Label
var _best_value: Label
var _next_icon: TextureRect
var _next_name: Label
var _danger_label: Label
var _combo_label: Label
var _menu_best: Label
var _continue_btn: Button
var _over_score: Label
var _over_best: Label
var _over_badge: Label
var _toggles: Dictionary = {}
var _lang_btns: Dictionary = {}
var _after_tutorial: Callable
var _safe_top := 0.0
var _safe_bottom := 0.0
var _last_combo := 0


func _init() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	layer = 10


func _ready() -> void:
	_root = Control.new()
	_root.theme = UITheme.make()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_root)
	_build_hud()
	_build_menu()
	_build_pause()
	_build_game_over()
	_build_tutorial()
	_build_settings()
	Settings.changed.connect(_refresh_settings)
	SaveData.best_changed.connect(func(_b: int) -> void: _refresh_numbers())
	_refresh_settings()
	_show_menu()


func bind(p_game: Game) -> void:
	game = p_game
	game.score_changed.connect(_on_score)
	game.next_fruit_changed.connect(_on_next)
	game.merged.connect(_on_merged)
	game.danger_changed.connect(_on_danger)
	game.game_over.connect(_on_game_over)
	game.state_changed.connect(_on_state)


func apply_layout(_viewport: Vector2, safe_top: float, safe_bottom: float) -> void:
	_safe_top = safe_top
	_safe_bottom = safe_bottom
	_hud.offset_top = safe_top
	_hud.offset_bottom = safe_top + HUD_H
	for screen: Control in [_menu, _pause, _settings, _tutorial, _over]:
		var m: MarginContainer = screen.get_meta("margin")
		m.add_theme_constant_override("margin_top", int(safe_top) + 24)
		m.add_theme_constant_override("margin_bottom", int(safe_bottom) + 24)


func _notification(what: int) -> void:
	if what == NOTIFICATION_TRANSLATION_CHANGED and _root != null:
		_refresh_numbers()


# ---------------------------------------------------------------- builders

func _label(text: String, size: int, color: Color = UITheme.INK) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	return l


func _number(size: int) -> Label:
	var l := _label("0", size)
	l.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	return l


func _button(key: String, action: Callable, is_secondary: bool = false) -> Button:
	var b := Button.new()
	b.text = key
	b.custom_minimum_size = BTN_SIZE
	b.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	if is_secondary:
		UITheme.secondary(b)
	b.pressed.connect(func() -> void:
		AudioManager.play_sfx("click")
		action.call())
	return b


## Full-screen layer with a centred column. `dim` < 1 keeps the board visible behind a dialog.
func _screen(dim: float, in_panel: bool) -> VBoxContainer:
	var screen := Control.new()
	screen.set_anchors_preset(Control.PRESET_FULL_RECT)
	screen.visible = false
	_root.add_child(screen)
	var bg := ColorRect.new()
	bg.color = Color(UITheme.CREAM, dim) if not in_panel else Color(0.16, 0.1, 0.05, dim)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_STOP
	screen.add_child(bg)
	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 40)
	margin.add_theme_constant_override("margin_right", 40)
	screen.add_child(margin)
	screen.set_meta("margin", margin)
	var center := CenterContainer.new()
	margin.add_child(center)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 22)
	col.alignment = BoxContainer.ALIGNMENT_CENTER
	if in_panel:
		var panel := PanelContainer.new()
		panel.custom_minimum_size = Vector2(600, 0)
		center.add_child(panel)
		panel.add_child(col)
		screen.set_meta("panel", panel)
	else:
		center.add_child(col)
	col.set_meta("screen", screen)
	return col


func _build_hud() -> void:
	_hud = Control.new()
	_hud.anchor_right = 1.0
	_hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hud.visible = false
	_root.add_child(_hud)
	var row := HBoxContainer.new()
	row.set_anchors_preset(Control.PRESET_FULL_RECT)
	row.offset_left = 32
	row.offset_right = -32
	row.offset_top = 16
	row.offset_bottom = -34
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hud.add_child(row)

	var left := VBoxContainer.new()
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left.add_theme_constant_override("separation", -6)
	left.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(left)
	var cap := _label("UI_SCORE", 26, Color("6b4a2b"))
	cap.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	left.add_child(cap)
	_score_value = _number(76)
	_score_value.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	left.add_child(_score_value)
	_best_value = _number(26)
	_best_value.add_theme_color_override("font_color", Color("6b4a2b"))
	_best_value.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	left.add_child(_best_value)

	var next_box := VBoxContainer.new()
	next_box.custom_minimum_size = Vector2(190, 0)
	next_box.alignment = BoxContainer.ALIGNMENT_CENTER
	next_box.add_theme_constant_override("separation", 0)
	next_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(next_box)
	next_box.add_child(_label("UI_NEXT", 26, Color("6b4a2b")))
	_next_icon = TextureRect.new()
	_next_icon.custom_minimum_size = Vector2(76, 76)
	_next_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_next_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_next_icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	next_box.add_child(_next_icon)
	_next_name = _label("", 22, Color("6b4a2b"))
	next_box.add_child(_next_name)

	var pause_btn := Button.new()
	pause_btn.custom_minimum_size = Vector2(96, 96)
	pause_btn.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	pause_btn.tooltip_text = "UI_PAUSE"
	pause_btn.accessibility_name = "UI_PAUSE"
	pause_btn.draw.connect(func() -> void:
		var s := pause_btn.size
		pause_btn.draw_rect(Rect2(s.x * 0.32, s.y * 0.28, s.x * 0.12, s.y * 0.44), Color.WHITE)
		pause_btn.draw_rect(Rect2(s.x * 0.56, s.y * 0.28, s.x * 0.12, s.y * 0.44), Color.WHITE))
	pause_btn.pressed.connect(func() -> void:
		AudioManager.play_sfx("click")
		game.pause())
	row.add_child(pause_btn)

	_danger_label = _label("UI_DANGER", 34, Color.WHITE)
	_danger_label.add_theme_color_override("font_outline_color", Color("8f1d12"))
	_danger_label.add_theme_constant_override("outline_size", 14)
	_danger_label.anchor_right = 1.0
	_danger_label.offset_top = HUD_H - 40.0
	_danger_label.offset_bottom = HUD_H + 8.0
	_danger_label.visible = false
	_hud.add_child(_danger_label)

	_combo_label = _number(40)
	_combo_label.add_theme_color_override("font_color", Color.WHITE)
	_combo_label.add_theme_color_override("font_outline_color", UITheme.ACCENT)
	_combo_label.add_theme_constant_override("outline_size", 14)
	_combo_label.anchor_right = 1.0
	_combo_label.offset_top = HUD_H - 44.0
	_combo_label.offset_bottom = HUD_H + 8.0
	_combo_label.modulate.a = 0.0
	_hud.add_child(_combo_label)


func _build_menu() -> void:
	var col := _screen(1.0, false)
	_menu = col.get_meta("screen")
	if ResourceLoader.exists("res://assets/icon/launch_logo.png"):
		var logo := TextureRect.new()
		logo.texture = load("res://assets/icon/launch_logo.png")
		logo.custom_minimum_size = Vector2(300, 300)
		logo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		logo.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		col.add_child(logo)
	var title := _label("Fruit Fusion", 84)
	title.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	col.add_child(title)
	col.add_child(_label("UI_TAGLINE", 32, Color("6b4a2b")))
	_menu_best = _number(34)
	col.add_child(_menu_best)
	var gap := Control.new()
	gap.custom_minimum_size = Vector2(0, 20)
	col.add_child(gap)
	_continue_btn = _button("UI_CONTINUE", _continue_run)
	col.add_child(_continue_btn)
	col.add_child(_button("UI_PLAY", _play))
	col.add_child(_button("UI_HOW_TO_PLAY", func() -> void: _open_tutorial(Callable()), true))
	col.add_child(_button("UI_SETTINGS", func() -> void: _open(_settings), true))


func _build_pause() -> void:
	var col := _screen(0.55, true)
	_pause = col.get_meta("screen")
	col.add_child(_label("UI_PAUSED", 56))
	col.add_child(_button("UI_RESUME", func() -> void: game.resume()))
	col.add_child(_button("UI_RESTART", _restart, true))
	col.add_child(_button("UI_SETTINGS", func() -> void: _open(_settings), true))
	col.add_child(_button("UI_MAIN_MENU", _show_menu, true))


func _build_game_over() -> void:
	var col := _screen(0.55, true)
	_over = col.get_meta("screen")
	col.add_child(_label("UI_GAME_OVER", 56))
	_over_badge = _label("UI_NEW_BEST", 38, UITheme.ACCENT)
	col.add_child(_over_badge)
	col.add_child(_label("UI_SCORE", 28, Color("6b4a2b")))
	_over_score = _number(110)
	col.add_child(_over_score)
	_over_best = _number(32)
	col.add_child(_over_best)
	col.add_child(_button("UI_PLAY_AGAIN", _restart))
	col.add_child(_button("UI_MAIN_MENU", _show_menu, true))


func _build_tutorial() -> void:
	var col := _screen(0.6, true)
	_tutorial = col.get_meta("screen")
	col.add_child(_label("UI_HOW_TO_PLAY", 52))
	var steps := [["UI_TUT_1", [3]], ["UI_TUT_2", [2, 2, 3]], ["UI_TUT_3", [6]]]
	for i in steps.size():
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 20)
		col.add_child(row)
		var num := _label(str(i + 1), 44, Color.WHITE)
		num.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
		num.custom_minimum_size = Vector2(64, 64)
		num.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		num.add_theme_stylebox_override("normal", UITheme.box(UITheme.PRIMARY, 32))
		num.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(num)
		var text := _label(steps[i][0], 30)
		text.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
		text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		text.custom_minimum_size = Vector2(330, 0)
		text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(text)
		var icons := HBoxContainer.new()
		icons.add_theme_constant_override("separation", 2)
		icons.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(icons)
		var tiers: Array = steps[i][1]
		for j in tiers.size():
			var path := FruitCatalog.texture_path(tiers[j])
			if not ResourceLoader.exists(path):
				continue
			var icon := TextureRect.new()
			icon.texture = load(path)
			var s := 64.0 if j == tiers.size() - 1 and tiers.size() != 1 else 44.0
			if tiers.size() == 1:
				s = 72.0
			icon.custom_minimum_size = Vector2(s, s)
			icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
			icons.add_child(icon)
	col.add_child(_button("UI_GOT_IT", _close_tutorial))


func _build_settings() -> void:
	var col := _screen(0.6, true)
	_settings = col.get_meta("screen")
	col.add_child(_label("UI_SETTINGS", 52))
	_toggle_row(col, "UI_SOUND", "sfx", func(on: bool) -> void: Settings.set_sfx(on))
	_toggle_row(col, "UI_MUSIC", "music", func(on: bool) -> void: Settings.set_music(on))
	_toggle_row(col, "UI_HAPTICS", "haptics", func(on: bool) -> void:
		Settings.set_haptics(on)
		Haptics.medium())
	col.add_child(_label("UI_LANGUAGE", 30, Color("6b4a2b")))
	var langs := HBoxContainer.new()
	langs.add_theme_constant_override("separation", 16)
	langs.alignment = BoxContainer.ALIGNMENT_CENTER
	col.add_child(langs)
	for pair in [["tr", "Türkçe"], ["en", "English"]]:
		var code: String = pair[0]
		var b := Button.new()
		b.text = pair[1]
		b.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
		b.custom_minimum_size = Vector2(250, 96)
		b.pressed.connect(func() -> void:
			AudioManager.play_sfx("click")
			Settings.set_language(code))
		langs.add_child(b)
		_lang_btns[code] = b
	col.add_child(_button("UI_CLOSE", func() -> void: _close(_settings)))


func _toggle_row(col: VBoxContainer, key: String, id: String, on_set: Callable) -> void:
	var row := HBoxContainer.new()
	col.add_child(row)
	var l := _label(key, 34)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(l)
	var b := Button.new()
	b.toggle_mode = true
	b.custom_minimum_size = Vector2(190, 92)
	b.toggled.connect(func(on: bool) -> void:
		on_set.call(on)
		AudioManager.play_sfx("click"))
	row.add_child(b)
	_toggles[id] = b


# ---------------------------------------------------------------- refresh

func _refresh_settings() -> void:
	var states := {"sfx": Settings.sfx_on, "music": Settings.music_on, "haptics": Settings.haptics_on}
	for id: String in _toggles:
		var b: Button = _toggles[id]
		var on: bool = states[id]
		b.set_pressed_no_signal(on)
		b.text = "UI_ON" if on else "UI_OFF"
		_style_choice(b, on)
	for code: String in _lang_btns:
		_style_choice(_lang_btns[code], code == Settings.language)


## Selected = filled primary, unselected = light outline; the label text also states the value.
func _style_choice(b: Button, selected: bool) -> void:
	for s in ["normal", "hover", "pressed"]:
		b.remove_theme_stylebox_override(s)
	for c in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color", "font_hover_pressed_color"]:
		b.remove_theme_color_override(c)
	if not selected:
		UITheme.secondary(b)


func _refresh_numbers() -> void:
	var best := "%s: %d" % [tr("UI_BEST"), SaveData.best_score]
	_best_value.text = best
	_menu_best.text = best
	_over_best.text = best
	_menu_best.visible = SaveData.best_score > 0
	if _last_combo > 1:
		_combo_label.text = "%s ×%d" % [tr("UI_COMBO"), _last_combo]


# ---------------------------------------------------------------- navigation

func _open(screen: Control) -> void:
	screen.visible = true
	screen.move_to_front()
	if screen.has_meta("panel"):
		var p: Control = screen.get_meta("panel")
		p.pivot_offset = p.size * 0.5
		p.scale = Vector2.ONE * 0.9
		p.modulate.a = 0.0
		var tw := p.create_tween().set_parallel()
		tw.tween_property(p, "scale", Vector2.ONE, 0.16).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_BACK)
		tw.tween_property(p, "modulate:a", 1.0, 0.12)


func _close(screen: Control) -> void:
	screen.visible = false


func _show_menu() -> void:
	if game != null:
		game.quit_to_menu()
	_close(_pause)
	_close(_over)
	_hud.visible = false
	_continue_btn.visible = SaveData.has_run()
	_refresh_numbers()
	_menu.visible = true


func _play() -> void:
	if not Settings.tutorial_seen:
		_open_tutorial(_start_new)
	else:
		_start_new()


func _start_new() -> void:
	_enter_game()
	game.start_new_game()


func _continue_run() -> void:
	_enter_game()
	if not game.resume_saved_game():
		game.start_new_game()


func _restart() -> void:
	game.resume()
	_enter_game()
	game.start_new_game()


func _enter_game() -> void:
	_menu.visible = false
	_close(_pause)
	_close(_over)
	_hud.visible = true
	_danger_label.visible = false
	_last_combo = 0
	_combo_label.modulate.a = 0.0
	_refresh_numbers()


func _open_tutorial(then: Callable) -> void:
	_after_tutorial = then
	_open(_tutorial)


func _close_tutorial() -> void:
	_close(_tutorial)
	Settings.set_tutorial_seen(true)
	var then := _after_tutorial
	_after_tutorial = Callable()
	if then.is_valid():
		then.call()


# ---------------------------------------------------------------- game events

func _on_state(state: int) -> void:
	if state == Game.State.PAUSED:
		_open(_pause)
	elif state == Game.State.PLAYING:
		_close(_pause)
		_close(_settings)


func _on_score(score: int) -> void:
	_score_value.text = str(score)
	_score_value.pivot_offset = Vector2(0, _score_value.size.y * 0.5)
	var tw := _score_value.create_tween()
	tw.tween_property(_score_value, "scale", Vector2.ONE * 1.12, 0.06)
	tw.tween_property(_score_value, "scale", Vector2.ONE, 0.1)


func _on_next(tier: int) -> void:
	var path := FruitCatalog.texture_path(tier)
	_next_icon.texture = load(path) if ResourceLoader.exists(path) else null
	_next_name.text = FruitCatalog.name_key(tier)


func _on_merged(_tier: int, _points: int, combo: int, _pos: Vector2) -> void:
	_last_combo = combo
	if combo < 2 or _danger_label.visible:
		return
	_combo_label.text = "%s ×%d" % [tr("UI_COMBO"), combo]
	_combo_label.modulate.a = 1.0
	var tw := _combo_label.create_tween()
	tw.tween_interval(0.7)
	tw.tween_property(_combo_label, "modulate:a", 0.0, 0.3)


func _on_danger(ratio: float) -> void:
	_danger_label.visible = ratio >= 0.25
	if _danger_label.visible:
		_combo_label.modulate.a = 0.0
		_danger_label.modulate.a = 0.65 + 0.35 * sin(ratio * 40.0)


func _on_game_over(score: int, is_new_best: bool) -> void:
	_danger_label.visible = false
	_over_score.text = str(score)
	_over_badge.visible = is_new_best
	_refresh_numbers()
	await get_tree().create_timer(0.7).timeout
	if game.state == Game.State.GAME_OVER:
		_open(_over)
