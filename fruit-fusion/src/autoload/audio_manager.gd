extends Node
## Sound effects and music with independent toggles (see Settings).

const SFX_NAMES: Array[String] = ["drop", "merge", "fusion", "click", "warning", "gameover", "newbest"]
const MUSIC_PATH := "res://assets/audio/music_loop.ogg"
const VOICES := 8

var _streams: Dictionary = {}
var _players: Array[AudioStreamPlayer] = []
var _next_voice := 0
var _music: AudioStreamPlayer


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_ensure_bus("SFX")
	_ensure_bus("Music")
	for n in SFX_NAMES:
		var path := "res://assets/audio/sfx_%s.wav" % n
		if ResourceLoader.exists(path):
			_streams[n] = load(path)
	for i in VOICES:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_music = AudioStreamPlayer.new()
	_music.bus = "Music"
	_music.volume_db = -8.0
	add_child(_music)
	if ResourceLoader.exists(MUSIC_PATH):
		_music.stream = load(MUSIC_PATH)
	Settings.changed.connect(_apply)
	_apply()


func _ensure_bus(bus_name: String) -> void:
	if AudioServer.get_bus_index(bus_name) != -1:
		return
	AudioServer.add_bus()
	var idx := AudioServer.bus_count - 1
	AudioServer.set_bus_name(idx, bus_name)
	AudioServer.set_bus_send(idx, "Master")


func _apply() -> void:
	AudioServer.set_bus_mute(AudioServer.get_bus_index("SFX"), not Settings.sfx_on)
	if _music.stream == null:
		return
	if Settings.music_on and not _music.playing:
		_music.play()
	elif not Settings.music_on and _music.playing:
		_music.stop()


func has_sfx(sfx: String) -> bool:
	return _streams.has(sfx)


func play_sfx(sfx: String, pitch: float = 1.0, volume_db: float = 0.0) -> void:
	if not Settings.sfx_on or not _streams.has(sfx):
		return
	var p := _players[_next_voice]
	_next_voice = (_next_voice + 1) % VOICES
	p.stream = _streams[sfx]
	p.pitch_scale = clampf(pitch, 0.25, 4.0)
	p.volume_db = volume_db
	p.play()
