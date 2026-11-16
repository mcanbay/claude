class_name DropQueue
extends RefCounted
## Seeded generator of the fruits handed to the player. `peek()` is what the HUD shows as "next".

var _rng := RandomNumberGenerator.new()
var _upcoming := 1


func _init(p_seed: int = 0) -> void:
	_rng.seed = p_seed
	_upcoming = _roll()


func peek() -> int:
	return _upcoming


func pop() -> int:
	var t := _upcoming
	_upcoming = _roll()
	return t


func _roll() -> int:
	var total := 0
	for w in FruitCatalog.DROP_WEIGHTS:
		total += w
	var r := _rng.randi_range(0, total - 1)
	for i in FruitCatalog.DROP_WEIGHTS.size():
		r -= FruitCatalog.DROP_WEIGHTS[i]
		if r < 0:
			return i + 1
	return 1


## 64-bit values are stored as strings because JSON numbers are doubles.
func to_dict() -> Dictionary:
	return {"seed": str(_rng.seed), "state": str(_rng.state), "upcoming": _upcoming}


static func from_dict(d: Dictionary) -> DropQueue:
	var q := DropQueue.new(str(d.get("seed", "0")).to_int())
	q._rng.state = str(d.get("state", "0")).to_int()
	var up := int(d.get("upcoming", 1))
	q._upcoming = clampi(up, 1, FruitCatalog.max_drop_tier())
	return q
