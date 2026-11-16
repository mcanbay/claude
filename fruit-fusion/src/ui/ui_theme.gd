class_name UITheme
extends RefCounted
## Shared look for all screens. Text colours keep ≥ 4.5:1 contrast on their backgrounds.

const INK := Color("3b2a1a")
const CREAM := Color("fdf2de")
const PANEL := Color("fff9ee")
const PRIMARY := Color("1f7a6f")
const PRIMARY_DARK := Color("165a52")
const ACCENT := Color("c2410c")
const SOFT := Color("efdfc2")


static func box(color: Color, radius: int = 28, border: Color = Color.TRANSPARENT, border_w: int = 0) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = color
	sb.set_corner_radius_all(radius)
	sb.set_content_margin_all(18)
	sb.content_margin_left = 28
	sb.content_margin_right = 28
	sb.border_color = border
	sb.set_border_width_all(border_w)
	sb.anti_aliasing = true
	return sb


static func make() -> Theme:
	var t := Theme.new()
	t.default_font_size = 34
	t.set_color("font_color", "Label", INK)
	t.set_stylebox("normal", "Button", box(PRIMARY))
	t.set_stylebox("hover", "Button", box(PRIMARY))
	t.set_stylebox("pressed", "Button", box(PRIMARY_DARK))
	t.set_stylebox("disabled", "Button", box(SOFT))
	t.set_stylebox("focus", "Button", box(Color.TRANSPARENT, 28, INK, 4))
	for c in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color", "font_hover_pressed_color"]:
		t.set_color(c, "Button", Color.WHITE)
	t.set_font_size("font_size", "Button", 38)
	var panel := box(PANEL, 40, Color("d9c39a"), 4)
	panel.set_content_margin_all(36)
	panel.shadow_color = Color(0.2, 0.12, 0.05, 0.25)
	panel.shadow_size = 18
	t.set_stylebox("panel", "PanelContainer", panel)
	return t


## Restyles a button as a quiet secondary action (dark text on a light surface).
static func secondary(b: Button) -> void:
	b.add_theme_stylebox_override("normal", box(SOFT, 28, Color("cdb88e"), 3))
	b.add_theme_stylebox_override("hover", box(SOFT, 28, Color("cdb88e"), 3))
	b.add_theme_stylebox_override("pressed", box(Color("e0cda6"), 28, Color("cdb88e"), 3))
	for c in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color", "font_hover_pressed_color"]:
		b.add_theme_color_override(c, INK)
