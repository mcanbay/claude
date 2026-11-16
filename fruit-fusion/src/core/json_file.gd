class_name JsonFile
extends RefCounted
## Small, corruption-tolerant JSON persistence helper.


static func read(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return {}
	var json := JSON.new()
	if json.parse(f.get_as_text()) != OK:
		return {}
	return json.data if json.data is Dictionary else {}


## Writes to a temp file first so a crash mid-write cannot corrupt the previous save.
static func write(path: String, data: Dictionary) -> bool:
	var tmp := path + ".tmp"
	var f := FileAccess.open(tmp, FileAccess.WRITE)
	if f == null:
		return false
	f.store_string(JSON.stringify(data))
	f.close()
	var dir := DirAccess.open(path.get_base_dir())
	if dir == null:
		return false
	return dir.rename(tmp.get_file(), path.get_file()) == OK
