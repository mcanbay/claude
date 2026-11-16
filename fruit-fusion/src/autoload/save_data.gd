extends Node
## Best score, statistics and the suspended run, persisted to user://save.json.

signal best_changed(best: int)

const VERSION := 1

var file_path := "user://save.json"
var best_score := 0
var games_played := 0
var saved_run: Dictionary = {}


func _ready() -> void:
	load_data()


func load_data() -> void:
	var d := JsonFile.read(file_path)
	best_score = maxi(int(d.get("best_score", 0)), 0)
	games_played = maxi(int(d.get("games_played", 0)), 0)
	var run: Variant = d.get("run", {})
	saved_run = run if run is Dictionary else {}


func save_data() -> void:
	JsonFile.write(file_path, {
		"version": VERSION, "best_score": best_score, "games_played": games_played, "run": saved_run,
	})


## Records a finished game's score. Returns true if it is a new best.
func submit_score(score: int) -> bool:
	var is_best := score > best_score
	if is_best:
		best_score = score
		best_changed.emit(best_score)
	save_data()
	return is_best


func has_run() -> bool:
	return not saved_run.is_empty()


func save_run(run: Dictionary) -> void:
	saved_run = run
	save_data()


func clear_run() -> void:
	if saved_run.is_empty():
		return
	saved_run = {}
	save_data()


func note_game_started() -> void:
	games_played += 1
	save_data()
