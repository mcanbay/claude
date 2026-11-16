class_name FruitCatalog
extends RefCounted
## Static data for the fruit ladder. Tiers are 1-based.

const MAX_TIER := 11
const RADII: Array[float] = [24.0, 33.0, 43.0, 54.0, 66.0, 80.0, 95.0, 111.0, 128.0, 146.0, 165.0]
const COLORS: Array[Color] = [
	Color("4a5fc1"), Color("b3122f"), Color("f6a43c"), Color("f4dc3a"), Color("f07f1c"), Color("c62a4b"),
	Color("f7a58c"), Color("d9c13f"), Color("7a5236"), Color("e8c98a"), Color("e0408f"),
]
## Relative weights of the tiers the player can be handed (tier 1..N).
const DROP_WEIGHTS: Array[int] = [35, 30, 20, 10, 5]


static func is_valid(tier: int) -> bool:
	return tier >= 1 and tier <= MAX_TIER


static func radius(tier: int) -> float:
	return RADII[clampi(tier, 1, MAX_TIER) - 1]


static func color(tier: int) -> Color:
	return COLORS[clampi(tier, 1, MAX_TIER) - 1]


static func name_key(tier: int) -> String:
	return "FRUIT_%d" % clampi(tier, 1, MAX_TIER)


static func texture_path(tier: int) -> String:
	return "res://assets/fruits/fruit_%02d.png" % clampi(tier, 1, MAX_TIER)


## Tier produced when two fruits of `tier` merge; 0 means both vanish (Fusion Burst).
static func next_tier(tier: int) -> int:
	return tier + 1 if tier < MAX_TIER else 0


static func max_drop_tier() -> int:
	return DROP_WEIGHTS.size()
