extends Node
## Saves and loads glades (binary dictionaries) with a PNG thumbnail each.

const DIR := "user://glades/"
const PHOTO_DIR := "user://photos/"


func _ready() -> void:
	DirAccess.make_dir_recursive_absolute(DIR)
	DirAccess.make_dir_recursive_absolute(PHOTO_DIR)


func new_id() -> String:
	return "glade_%d_%04d" % [int(Time.get_unix_time_from_system()), randi() % 10000]


func save(id: String, data: Dictionary, thumb: Image = null) -> void:
	var f := FileAccess.open(DIR + id + ".glade", FileAccess.WRITE)
	if f == null:
		push_warning("Could not save glade " + id)
		return
	data["saved_at"] = Time.get_unix_time_from_system()
	f.store_var(data, false)
	f.close()
	if thumb:
		thumb.save_png(DIR + id + ".png")


func load_glade(id: String) -> Dictionary:
	var f := FileAccess.open(DIR + id + ".glade", FileAccess.READ)
	if f == null:
		return {}
	var v = f.get_var(false)
	f.close()
	return v if v is Dictionary else {}


func delete(id: String) -> void:
	DirAccess.remove_absolute(DIR + id + ".glade")
	if FileAccess.file_exists(DIR + id + ".png"):
		DirAccess.remove_absolute(DIR + id + ".png")


## Returns [{id, name, saved_at, thumb: Texture2D or null}] newest first.
func list_glades() -> Array:
	var out: Array = []
	var dir := DirAccess.open(DIR)
	if dir == null:
		return out
	for file in dir.get_files():
		if not file.ends_with(".glade"):
			continue
		var id := file.get_basename()
		var f := FileAccess.open(DIR + file, FileAccess.READ)
		if f == null:
			continue
		var v = f.get_var(false)
		f.close()
		if not v is Dictionary:
			continue
		var thumb: Texture2D = null
		if FileAccess.file_exists(DIR + id + ".png"):
			var img := Image.load_from_file(DIR + id + ".png")
			if img:
				thumb = ImageTexture.create_from_image(img)
		out.append({"id": id, "name": v.get("name", "Glade"), "saved_at": v.get("saved_at", 0.0), "thumb": thumb})
	out.sort_custom(func(a, b): return a.saved_at > b.saved_at)
	return out


func last_glade_id() -> String:
	var all := list_glades()
	return all[0].id if not all.is_empty() else ""


## Stores a photo-mode capture. Tries the shared Pictures folder first so it
## shows up in the phone's gallery, then falls back to app storage.
func save_photo(img: Image) -> String:
	var stamp := Time.get_datetime_string_from_system().replace(":", "-")
	var name := "Everglade_%s.png" % stamp
	var pictures := OS.get_system_dir(OS.SYSTEM_DIR_PICTURES)
	if pictures != "":
		var target := pictures.path_join("Everglade")
		DirAccess.make_dir_recursive_absolute(target)
		if img.save_png(target.path_join(name)) == OK:
			return target.path_join(name)
	img.save_png(PHOTO_DIR + name)
	return ProjectSettings.globalize_path(PHOTO_DIR + name)
