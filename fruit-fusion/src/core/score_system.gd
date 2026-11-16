class_name ScoreSystem
extends RefCounted
## Score and chain-combo rules.

const FUSION_BONUS := 150
const COMBO_WINDOW := 1.0
const COMBO_STEP := 0.5
const MAX_MULTIPLIER := 3.0

var score := 0
var combo := 0
var _combo_left := 0.0


## Base points for creating a fruit of `tier` (triangular numbers).
static func points_for_created(tier: int) -> int:
	return tier * (tier + 1) / 2


## Base points for merging two fruits of `tier`.
static func base_points_for_merge(tier: int) -> int:
	var created := FruitCatalog.next_tier(tier)
	return FUSION_BONUS if created == 0 else points_for_created(created)


static func multiplier(combo_count: int) -> float:
	return minf(1.0 + COMBO_STEP * maxi(combo_count - 1, 0), MAX_MULTIPLIER)


func reset() -> void:
	score = 0
	combo = 0
	_combo_left = 0.0


func tick(delta: float) -> void:
	if _combo_left > 0.0:
		_combo_left -= delta
		if _combo_left <= 0.0:
			combo = 0


## Registers a merge of two `tier` fruits and returns the points awarded.
func register_merge(tier: int) -> int:
	combo += 1
	_combo_left = COMBO_WINDOW
	var points := roundi(base_points_for_merge(tier) * multiplier(combo))
	score += points
	return points
