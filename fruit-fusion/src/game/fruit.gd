class_name Fruit
extends RigidBody2D
## One fruit. Merging is decided by Game/MergeResolver, never inside physics callbacks.

const GROW_TIME := 0.12
const GROW_START := 0.7
const MASS_PER_AREA := 0.001

static var _tex_cache: Dictionary = {}
static var _material: PhysicsMaterial

var uid := 0
var tier := 1
var radius := 24.0
## Set the instant a merge is accepted; a consumed fruit can never merge again.
var consumed := false
## True once the fruit has touched something after being dropped.
var landed := false
var held := false

var _shape: CircleShape2D
var _sprite: Sprite2D
var _grow := 1.0


static func create(p_uid: int, p_tier: int) -> Fruit:
	var f := Fruit.new()
	f.uid = p_uid
	f.tier = p_tier
	f.radius = FruitCatalog.radius(p_tier)
	return f


func _init() -> void:
	if _material == null:
		_material = PhysicsMaterial.new()
		_material.friction = 0.45
		_material.bounce = 0.12
	physics_material_override = _material
	contact_monitor = true
	max_contacts_reported = 8
	linear_damp = 0.15
	angular_damp = 1.2


func _ready() -> void:
	mass = maxf(radius * radius * MASS_PER_AREA, 0.1)
	_shape = CircleShape2D.new()
	_shape.radius = radius
	var cs := CollisionShape2D.new()
	cs.shape = _shape
	add_child(cs)
	var tex := _texture(tier)
	if tex != null:
		_sprite = Sprite2D.new()
		_sprite.texture = tex
		_sprite.scale = Vector2.ONE * (radius * 2.0 / tex.get_width())
		add_child(_sprite)


static func _texture(p_tier: int) -> Texture2D:
	if not _tex_cache.has(p_tier):
		var path := FruitCatalog.texture_path(p_tier)
		_tex_cache[p_tier] = load(path) if ResourceLoader.exists(path) else null
	return _tex_cache[p_tier]


## Vector fallback used only when the sprite is missing.
func _draw() -> void:
	if _sprite != null:
		return
	var c := FruitCatalog.color(tier)
	draw_circle(Vector2.ZERO, radius, c.darkened(0.25))
	draw_circle(Vector2.ZERO, radius * 0.92, c)
	draw_circle(Vector2(-radius * 0.3, -radius * 0.35), radius * 0.22, c.lightened(0.45))


func set_held() -> void:
	held = true
	freeze_mode = RigidBody2D.FREEZE_MODE_KINEMATIC
	freeze = true
	collision_layer = 0
	collision_mask = 0
	physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF


func release() -> void:
	held = false
	collision_layer = 1
	collision_mask = 1
	freeze = false
	linear_velocity = Vector2.ZERO
	angular_velocity = 0.0
	physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_INHERIT
	reset_physics_interpolation()


## Removes the fruit from the simulation immediately; the node is freed at end of frame.
func consume() -> void:
	consumed = true
	collision_layer = 0
	collision_mask = 0
	queue_free()


## Starts the collider small and grows it, so a freshly merged fruit pushes neighbours gently.
func begin_grow() -> void:
	_grow = 0.0
	if _shape != null:
		_shape.radius = radius * GROW_START
	pop()


func pop() -> void:
	var target: CanvasItem = _sprite if _sprite != null else self
	var base: Vector2 = target.scale
	target.scale = base * 0.6
	var tw := create_tween()
	tw.tween_property(target, "scale", base * 1.12, 0.09).set_ease(Tween.EASE_OUT)
	tw.tween_property(target, "scale", base, 0.08)


func _physics_process(delta: float) -> void:
	if _grow < 1.0:
		_grow = minf(_grow + delta / GROW_TIME, 1.0)
		_shape.radius = radius * lerpf(GROW_START, 1.0, _grow)
	if not held and not landed and get_contact_count() > 0:
		landed = true


func top_y() -> float:
	return position.y - radius
