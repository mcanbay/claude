class_name MergeEffects
extends Node2D
## Short-lived visual feedback for merges. Everything frees itself.

static var _dot: GradientTexture2D


func _ready() -> void:
	if _dot == null:
		var g := Gradient.new()
		g.set_color(0, Color.WHITE)
		g.set_color(1, Color(1, 1, 1, 0))
		_dot = GradientTexture2D.new()
		_dot.gradient = g
		_dot.fill = GradientTexture2D.FILL_RADIAL
		_dot.fill_from = Vector2(0.5, 0.5)
		_dot.fill_to = Vector2(1.0, 0.5)
		_dot.width = 32
		_dot.height = 32


func burst(pos: Vector2, color: Color, radius: float, big: bool = false) -> void:
	var p := CPUParticles2D.new()
	p.position = pos
	p.texture = _dot
	p.one_shot = true
	p.explosiveness = 1.0
	p.amount = 28 if big else 12
	p.lifetime = 0.7 if big else 0.45
	p.spread = 180.0
	p.gravity = Vector2(0, 500)
	p.emission_shape = CPUParticles2D.EMISSION_SHAPE_SPHERE
	p.emission_sphere_radius = radius * 0.5
	p.initial_velocity_min = 90.0 + radius
	p.initial_velocity_max = 220.0 + radius * 2.0
	p.scale_amount_min = 0.35
	p.scale_amount_max = 0.8 if not big else 1.2
	p.color = color.lightened(0.25)
	p.finished.connect(p.queue_free)
	add_child(p)
	p.emitting = true


func popup(pos: Vector2, text: String, size: int = 40) -> void:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", Color.WHITE)
	l.add_theme_color_override("font_outline_color", Color("3b2a1a"))
	l.add_theme_constant_override("outline_size", 10)
	add_child(l)
	l.position = pos - l.get_minimum_size() * 0.5
	var tw := l.create_tween()
	tw.tween_property(l, "position:y", l.position.y - 70.0, 0.7).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.parallel().tween_property(l, "modulate:a", 0.0, 0.3).set_delay(0.4)
	tw.tween_callback(l.queue_free)
