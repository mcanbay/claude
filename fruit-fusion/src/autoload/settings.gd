extends Node
## Player preferences, persisted to user://settings.json.

signal changed

const LANGUAGES: Array[String] = ["tr", "en"]

var file_path := "user://settings.json"
var sfx_on := true
var music_on := true
var haptics_on := true
var language := "tr"
var tutorial_seen := false


func _ready() -> void:
	language = default_language()
	load_settings()


## Turkish is the primary language; English is used on English-language devices.
static func default_language() -> String:
	return "en" if OS.get_locale_language() == "en" else "tr"


func load_settings() -> void:
	var d := JsonFile.read(file_path)
	sfx_on = bool(d.get("sfx_on", sfx_on))
	music_on = bool(d.get("music_on", music_on))
	haptics_on = bool(d.get("haptics_on", haptics_on))
	tutorial_seen = bool(d.get("tutorial_seen", tutorial_seen))
	var lang := str(d.get("language", language))
	language = lang if lang in LANGUAGES else default_language()
	TranslationServer.set_locale(language)
	changed.emit()


func save_settings() -> void:
	JsonFile.write(file_path, {
		"sfx_on": sfx_on, "music_on": music_on, "haptics_on": haptics_on,
		"language": language, "tutorial_seen": tutorial_seen,
	})


func set_sfx(on: bool) -> void:
	sfx_on = on
	_commit()


func set_music(on: bool) -> void:
	music_on = on
	_commit()


func set_haptics(on: bool) -> void:
	haptics_on = on
	_commit()


func set_language(lang: String) -> void:
	if lang not in LANGUAGES:
		return
	language = lang
	TranslationServer.set_locale(lang)
	_commit()


func set_tutorial_seen(seen: bool) -> void:
	tutorial_seen = seen
	_commit()


func _commit() -> void:
	save_settings()
	changed.emit()
