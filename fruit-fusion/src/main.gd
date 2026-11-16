extends Node
## Root scene: backdrop, game, UI, and safe-area aware layout.

const UI_SCRIPT := "res://src/ui/ui_root.gd"
const BACKDROP := "res://assets/ui/jar_bg.png"
const HUD_HEIGHT := 200.0
const BOTTOM_MARGIN := 28.0

var game: Game
var ui: Node


func _ready() -> void:
	if ResourceLoader.exists(BACKDROP):
		var layer := CanvasLayer.new()
		layer.layer = -10
		add_child(layer)
		var bg := TextureRect.new()
		bg.texture = load(BACKDROP)
		bg.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		bg.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
		bg.set_anchors_preset(Control.PRESET_FULL_RECT)
		bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
		layer.add_child(bg)
	game = Game.new()
	game.name = "Game"
	add_child(game)
	if ResourceLoader.exists(UI_SCRIPT):
		ui = (load(UI_SCRIPT) as GDScript).new()
		ui.name = "UI"
		add_child(ui)
		ui.bind(game)
	get_viewport().size_changed.connect(_layout)
	_layout()
	if ui == null:
		game.start_new_game()


## Safe-area insets in canvas units: x = top, y = bottom.
## `--safe-top=N` / `--safe-bottom=N` (after `--`) simulate a notch and home indicator on desktop.
func safe_insets() -> Vector2:
	var top := 0.0
	var bottom := 0.0
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--safe-top="):
			top = a.get_slice("=", 1).to_float()
		elif a.begins_with("--safe-bottom="):
			bottom = a.get_slice("=", 1).to_float()
	if OS.has_feature("mobile"):
		var win := Vector2(DisplayServer.window_get_size())
		var safe := Rect2(DisplayServer.get_display_safe_area())
		var vp := get_viewport().get_visible_rect().size
		if win.y > 0.0 and safe.size.y > 0.0:
			var k := vp.y / win.y
			top = maxf(safe.position.y, 0.0) * k
			bottom = maxf(win.y - safe.end.y, 0.0) * k
	return Vector2(top, bottom)


func _layout() -> void:
	var vp := get_viewport().get_visible_rect().size
	var insets := safe_insets()
	var top := insets.x + HUD_HEIGHT
	var bottom := vp.y - insets.y - BOTTOM_MARGIN
	game.set_layout(Rect2(0.0, top, vp.x, maxf(bottom - top, 100.0)))
	if ui != null:
		ui.apply_layout(vp, insets.x, insets.y)
