class_name Board
extends Node2D
## The jar: fixed logical play field (W×H), walls, danger line and aim guide.
## All fruit positions are in this node's local space, so gameplay is identical on every screen.

const W := 640.0
const H := 900.0
const DANGER_Y := 150.0
const DROP_Y := 78.0
const WALL := 200.0
const RIM_Y := 34.0

var fruits_root: Node2D
var danger_ratio := 0.0:
	set(v):
		if not is_equal_approx(v, danger_ratio):
			danger_ratio = v
			queue_redraw()
var aim_x := -1.0:
	set(v):
		aim_x = v
		queue_redraw()
var aim_radius := 0.0

var _glass := StyleBoxFlat.new()


func _ready() -> void:
	var body := StaticBody2D.new()
	var mat := PhysicsMaterial.new()
	mat.friction = 0.5
	mat.bounce = 0.05
	body.physics_material_override = mat
	add_child(body)
	var tall := H + 4000.0
	_add_wall(body, Vector2(-WALL * 0.5, H - tall * 0.5), Vector2(WALL, tall))
	_add_wall(body, Vector2(W + WALL * 0.5, H - tall * 0.5), Vector2(WALL, tall))
	_add_wall(body, Vector2(W * 0.5, H + WALL * 0.5), Vector2(W + WALL * 2.0, WALL))
	fruits_root = Node2D.new()
	add_child(fruits_root)
	_glass.bg_color = Color(1, 1, 1, 0.42)
	_glass.border_color = Color("5b8f8a")
	_glass.set_border_width_all(8)
	_glass.border_width_top = 0
	_glass.corner_radius_bottom_left = 30
	_glass.corner_radius_bottom_right = 30
	_glass.anti_aliasing = true


func _add_wall(body: StaticBody2D, center: Vector2, size: Vector2) -> void:
	var shape := RectangleShape2D.new()
	shape.size = size
	var cs := CollisionShape2D.new()
	cs.shape = shape
	cs.position = center
	body.add_child(cs)


## Scales and centres the field inside `rect` (canvas coordinates).
func fit(rect: Rect2) -> void:
	var s := minf(rect.size.x / (W + 16.0), rect.size.y / (H + 8.0))
	scale = Vector2.ONE * s
	position = rect.position + (rect.size - Vector2(W, H) * s) * 0.5
	reset_physics_interpolation()


func _draw() -> void:
	draw_style_box(_glass, Rect2(-8.0, RIM_Y, W + 16.0, H - RIM_Y + 8.0))
	# Rim lips.
	var rim := Color("5b8f8a")
	draw_rect(Rect2(-16.0, RIM_Y - 10.0, 24.0, 14.0), rim)
	draw_rect(Rect2(W - 8.0, RIM_Y - 10.0, 24.0, 14.0), rim)
	if danger_ratio > 0.0:
		draw_rect(Rect2(0.0, RIM_Y, W, DANGER_Y - RIM_Y), Color(0.9, 0.15, 0.1, 0.28 * danger_ratio))
	var line := Color("b9772f").lerp(Color("d6261c"), danger_ratio)
	line.a = 0.55 + 0.45 * danger_ratio
	draw_dashed_line(Vector2(6.0, DANGER_Y), Vector2(W - 6.0, DANGER_Y), line, 4.0 + 3.0 * danger_ratio, 18.0)
	if aim_x >= 0.0:
		draw_dashed_line(Vector2(aim_x, DROP_Y + aim_radius + 6.0), Vector2(aim_x, H - 6.0),
				Color(0.25, 0.4, 0.4, 0.35), 3.0, 14.0)
