class_name Game
extends Node2D
## Game loop: drop input, deterministic merging, scoring, danger timer, save/restore.

signal score_changed(score: int)
signal best_changed(best: int)
signal next_fruit_changed(tier: int)
signal merged(tier: int, points: int, combo: int, pos: Vector2)
signal danger_changed(ratio: float)
signal game_over(score: int, is_new_best: bool)
signal state_changed(state: int)

enum State { IDLE, PLAYING, PAUSED, GAME_OVER }

const DROP_COOLDOWN := 0.5
const SAVE_VERSION := 1
const WARN_RATIO := 0.3
const MAX_SAVED_FRUITS := 400

var state: int = State.IDLE
var score: int:
	get:
		return _score.score
var board: Board
var effects: MergeEffects

var _score := ScoreSystem.new()
var _danger := DangerMonitor.new()
var _queue := DropQueue.new()
var _fruits: Dictionary = {}  # uid -> Fruit (dropped, alive)
var _next_uid := 1
var _held: Fruit
var _cooldown := 0.0
var _aim_x := Board.W * 0.5
var _touch := -1
var _warned := false
var _pairs: Array = []


func _ready() -> void:
	board = Board.new()
	add_child(board)
	effects = MergeEffects.new()
	board.add_child(effects)
	SaveData.best_changed.connect(func(b: int) -> void: best_changed.emit(b))


func set_layout(play_rect: Rect2) -> void:
	board.fit(play_rect)


# ---------------------------------------------------------------- lifecycle

func start_new_game(rng_seed: int = -1) -> void:
	_reset_run()
	SaveData.clear_run()
	SaveData.note_game_started()
	_queue = DropQueue.new(rng_seed if rng_seed >= 0 else randi())
	_spawn_held(_queue.pop())
	_set_state(State.PLAYING)
	score_changed.emit(0)


## Restores the suspended run. Returns false (and stays idle) if there is none or it is invalid.
func resume_saved_game() -> bool:
	var run := SaveData.saved_run
	if int(run.get("v", 0)) != SAVE_VERSION or not run.get("fruits") is Array or not run.get("queue") is Dictionary:
		SaveData.clear_run()
		return false
	_reset_run()
	_score.score = maxi(int(run.get("score", 0)), 0)
	_queue = DropQueue.from_dict(run["queue"])
	var list: Array = run["fruits"]
	for item: Variant in list.slice(0, MAX_SAVED_FRUITS):
		if not item is Array or item.size() < 3 or not FruitCatalog.is_valid(int(item[0])):
			continue
		var f := _add_fruit(int(item[0]), Vector2(float(item[1]), float(item[2])))
		f.rotation = float(item[3]) if item.size() > 3 else 0.0
	var held_tier := int(run.get("held", 0))
	if held_tier < 1 or held_tier > FruitCatalog.max_drop_tier():
		held_tier = _queue.pop()
	_spawn_held(held_tier)
	_set_state(State.PLAYING)
	score_changed.emit(_score.score)
	return true


func pause() -> void:
	if state != State.PLAYING:
		return
	_touch = -1
	save_run()
	get_tree().paused = true
	_set_state(State.PAUSED)


func resume() -> void:
	if state != State.PAUSED:
		return
	get_tree().paused = false
	_set_state(State.PLAYING)


## Leaves the run (saving it if still alive) and clears the board.
func quit_to_menu() -> void:
	if state == State.PLAYING or state == State.PAUSED:
		save_run()
	get_tree().paused = false
	_reset_run()
	_set_state(State.IDLE)


func save_run() -> void:
	if state != State.PLAYING and state != State.PAUSED:
		return
	var list: Array = []
	for f: Fruit in _fruits.values():
		list.append([f.tier, snappedf(f.position.x, 0.01), snappedf(f.position.y, 0.01), snappedf(f.rotation, 0.001)])
	SaveData.save_run({
		"v": SAVE_VERSION, "score": _score.score, "queue": _queue.to_dict(),
		"held": _held.tier if _held != null else 0, "fruits": list,
	})


func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_PAUSED or what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		if state == State.PLAYING:
			pause()
	elif what == NOTIFICATION_WM_CLOSE_REQUEST:
		save_run()


func _reset_run() -> void:
	for c in board.fruits_root.get_children():
		board.fruits_root.remove_child(c)
		c.queue_free()
	_fruits.clear()
	_held = null
	_next_uid = 1
	_cooldown = 0.0
	_touch = -1
	_warned = false
	_aim_x = Board.W * 0.5
	_score.reset()
	_danger.reset()
	board.danger_ratio = 0.0
	board.aim_x = -1.0
	danger_changed.emit(0.0)


func _set_state(s: int) -> void:
	if state != s:
		state = s
		state_changed.emit(s)


# ---------------------------------------------------------------- input / dropping

func _unhandled_input(event: InputEvent) -> void:
	if state != State.PLAYING:
		return
	if event is InputEventScreenTouch:
		var p := _to_board(event.position)
		if event.pressed:
			if _touch == -1 and p.y >= 0.0 and p.y <= Board.H + 60.0:
				_touch = event.index
				aim(p.x)
		elif event.index == _touch:
			_touch = -1
			aim(p.x)
			drop()
	elif event is InputEventScreenDrag and event.index == _touch:
		aim(_to_board(event.position).x)


func _to_board(canvas_pos: Vector2) -> Vector2:
	return board.get_global_transform().affine_inverse() * canvas_pos


## Moves the held fruit to board-local x (clamped to the jar).
func aim(x: float) -> void:
	var r := _held.radius if _held != null else FruitCatalog.radius(1)
	_aim_x = clampf(x, r + 2.0, Board.W - r - 2.0)
	if _held != null:
		_held.position.x = _aim_x
		board.aim_radius = r
		board.aim_x = _aim_x


## Releases the held fruit. Returns false if nothing can be dropped right now.
func drop() -> bool:
	if state != State.PLAYING or _held == null:
		return false
	var f := _held
	_held = null
	f.release()
	_fruits[f.uid] = f
	_cooldown = DROP_COOLDOWN
	board.aim_x = -1.0
	AudioManager.play_sfx("drop", randf_range(0.95, 1.08), -4.0)
	Haptics.light()
	return true


func _spawn_held(tier: int) -> void:
	var f := Fruit.create(_next_uid, tier)
	_next_uid += 1
	f.set_held()
	board.fruits_root.add_child(f)
	_held = f
	f.position = Vector2(_aim_x, Board.DROP_Y)
	aim(_aim_x)
	f.pop()
	next_fruit_changed.emit(_queue.peek())


func _add_fruit(tier: int, pos: Vector2) -> Fruit:
	var f := Fruit.create(_next_uid, tier)
	_next_uid += 1
	f.landed = true
	var r := f.radius
	f.position = Vector2(clampf(pos.x, r, Board.W - r), minf(pos.y, Board.H - r))
	board.fruits_root.add_child(f)
	f.reset_physics_interpolation()
	_fruits[f.uid] = f
	return f


# ---------------------------------------------------------------- simulation

func _physics_process(delta: float) -> void:
	if state != State.PLAYING:
		return
	_score.tick(delta)
	if _held == null:
		_cooldown -= delta
		if _cooldown <= 0.0:
			_spawn_held(_queue.pop())
	_resolve_merges()
	_update_danger(delta)


func _resolve_merges() -> void:
	_pairs.clear()
	for f: Fruit in _fruits.values():
		for b in f.get_colliding_bodies():
			var o := b as Fruit
			if o != null and o.tier == f.tier and f.uid < o.uid and not o.consumed and not o.held:
				_pairs.append(Vector3i(f.uid, o.uid, f.tier))
	if _pairs.is_empty():
		return
	for m in MergeResolver.resolve(_pairs):
		_merge(_fruits[m.x], _fruits[m.y])


func _merge(a: Fruit, b: Fruit) -> void:
	if a.consumed or b.consumed:
		return
	var tier := a.tier
	var pos := (a.position + b.position) * 0.5
	var vel := (a.linear_velocity + b.linear_velocity) * 0.5
	_fruits.erase(a.uid)
	_fruits.erase(b.uid)
	a.consume()
	b.consume()
	var points := _score.register_merge(tier)
	var created := FruitCatalog.next_tier(tier)
	var color := FruitCatalog.color(tier)
	if created > 0:
		var f := _add_fruit(created, pos)
		f.linear_velocity = vel
		f.begin_grow()
		pos = f.position
		effects.burst(pos, color, a.radius)
		AudioManager.play_sfx("merge", 1.45 - 0.07 * tier)
		if tier >= 6:
			Haptics.medium()
		else:
			Haptics.light()
	else:
		effects.burst(pos, color, a.radius, true)
		effects.burst(pos, Color("ffd34d"), a.radius, true)
		AudioManager.play_sfx("fusion")
		Haptics.heavy()
	var label := "+%d" % points
	if _score.combo > 1:
		label += "  ×%d" % _score.combo
	effects.popup(pos, label, 34 + mini(tier, 8) * 3)
	score_changed.emit(_score.score)
	merged.emit(tier, points, _score.combo, board.to_global(pos))


func _update_danger(delta: float) -> void:
	var over := false
	for f: Fruit in _fruits.values():
		if f.landed and f.top_y() < Board.DANGER_Y:
			over = true
			break
	var before := _danger.ratio()
	var dead := _danger.update(delta, over)
	var ratio := _danger.ratio()
	if not is_equal_approx(ratio, before):
		board.danger_ratio = ratio
		danger_changed.emit(ratio)
	if ratio >= WARN_RATIO and not _warned:
		_warned = true
		AudioManager.play_sfx("warning")
		Haptics.medium()
	elif ratio == 0.0:
		_warned = false
	if dead:
		_end_game()


func _end_game() -> void:
	if _held != null:
		_held.queue_free()
		_held = null
	board.aim_x = -1.0
	SaveData.clear_run()
	var is_best := SaveData.submit_score(_score.score)
	_set_state(State.GAME_OVER)
	AudioManager.play_sfx("newbest" if is_best else "gameover")
	Haptics.heavy()
	game_over.emit(_score.score, is_best)


# ---------------------------------------------------------------- test / tooling helpers

func fruit_count() -> int:
	return _fruits.size()


func fruit_tiers() -> Array[int]:
	var out: Array[int] = []
	for f: Fruit in _fruits.values():
		out.append(f.tier)
	out.sort()
	return out


func held_tier() -> int:
	return _held.tier if _held != null else 0


## Places a landed fruit directly on the board (tests, screenshots).
func debug_add_fruit(tier: int, pos: Vector2) -> Fruit:
	return _add_fruit(tier, pos)
