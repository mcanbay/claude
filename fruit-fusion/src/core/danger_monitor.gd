class_name DangerMonitor
extends RefCounted
## Game-over timer: fires when fruit stays above the danger line continuously for `limit` seconds.

var limit := 2.5
var elapsed := 0.0


func reset() -> void:
	elapsed = 0.0


func ratio() -> float:
	return clampf(elapsed / limit, 0.0, 1.0)


## Returns true when the limit has been reached.
func update(delta: float, any_over: bool) -> bool:
	if any_over:
		elapsed += delta
	else:
		elapsed = 0.0
	return elapsed >= limit
