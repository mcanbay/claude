extends Node
## Haptic feedback wrapper. No-op on platforms without a vibration motor or when disabled.

var enabled_for_platform := OS.has_feature("mobile")


func light() -> void:
	_buzz(12, 0.35)


func medium() -> void:
	_buzz(22, 0.6)


func heavy() -> void:
	_buzz(45, 1.0)


func _buzz(ms: int, amplitude: float) -> void:
	if Settings.haptics_on and enabled_for_platform:
		Input.vibrate_handheld(ms, amplitude)
