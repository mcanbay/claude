class_name MergeResolver
extends RefCounted
## Deterministic selection of merges for one physics tick.
##
## Input: touching same-tier pairs as Vector3i(uid_a, uid_b, tier), in any order, possibly duplicated.
## Output: accepted pairs as Vector3i(low_uid, high_uid, tier); every uid appears at most once.
## The result depends only on the set of pairs, never on their order.


static func resolve(pairs: Array) -> Array[Vector3i]:
	var seen := {}
	var unique: Array[Vector3i] = []
	for p: Vector3i in pairs:
		if p.x == p.y:
			continue
		var n := Vector3i(mini(p.x, p.y), maxi(p.x, p.y), p.z)
		if not seen.has(n):
			seen[n] = true
			unique.append(n)
	unique.sort_custom(_before)
	var used := {}
	var out: Array[Vector3i] = []
	for p in unique:
		if used.has(p.x) or used.has(p.y):
			continue
		used[p.x] = true
		used[p.y] = true
		out.append(p)
	return out


static func _before(a: Vector3i, b: Vector3i) -> bool:
	if a.z != b.z:
		return a.z > b.z
	if a.x != b.x:
		return a.x < b.x
	return a.y < b.y
