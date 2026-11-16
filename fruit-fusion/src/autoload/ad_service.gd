extends Node
## Extension point for future rewarded ads. Version 1 ships with no provider: nothing is loaded,
## no network access happens and every query reports "not available".
##
## To add ads later, implement an object with `is_ready(placement) -> bool` and
## `show(placement, on_done: Callable)` (on_done receives `granted: bool`) and call `set_provider()`.

signal rewarded_finished(placement: String, granted: bool)

const PLACEMENT_CONTINUE := "continue_after_game_over"

var _provider: Object = null


func set_provider(provider: Object) -> void:
	_provider = provider


func is_rewarded_ready(placement: String) -> bool:
	return _provider != null and _provider.is_ready(placement)


func show_rewarded(placement: String) -> void:
	if not is_rewarded_ready(placement):
		rewarded_finished.emit.call_deferred(placement, false)
		return
	_provider.show(placement, func(granted: bool) -> void: rewarded_finished.emit(placement, granted))
