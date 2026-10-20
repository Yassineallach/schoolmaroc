class_name SaveManager
extends Node

## Persists settings (shared), and per profile: lifetime stats, discoveries
## and the run in progress. Writes happen on a background thread; each file
## is compressed and written to a temp file that then replaces the old one,
## so a crash mid-write never leaves a broken save. Requests to the same
## file are coalesced: only the latest snapshot is written.

const PROFILES := 3
const SETTINGS_PATH := "user://settings.cfg"
const LEGACY_PATH := "user://stats.cfg"
const MAGIC := 0x414C4541  # "ALEA"
const VERSION := 1

var profile := 1

var _thread := Thread.new()
var _sem := Semaphore.new()
var _mutex := Mutex.new()
var _pending := {}  # path -> [seq, PackedByteArray or null (= delete)]
var _quit := false
var _seq := 0
var _io := Mutex.new()  # one write at a time, from either thread
var _written := {}  # path -> seq of the newest snapshot on disk


func _ready() -> void:
	_thread.start(_worker)


func _exit_tree() -> void:
	flush()
	_mutex.lock()
	_quit = true
	_mutex.unlock()
	_sem.post()
	_thread.wait_to_finish()


func _notification(what: int) -> void:
	# Android may kill a backgrounded app without warning.
	if what == NOTIFICATION_APPLICATION_PAUSED or what == NOTIFICATION_WM_CLOSE_REQUEST \
			or what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		flush()


# ---------------------------------------------------------------- paths

func _dir(p: int = profile) -> String:
	return "user://profile_%d" % p


func _profile_path(p: int = profile) -> String:
	return _dir(p) + "/profile.sav"


func _run_path(p: int = profile) -> String:
	return _dir(p) + "/run.sav"


# ---------------------------------------------------------------- settings

func load_settings(defaults: Dictionary) -> Dictionary:
	var out := defaults.duplicate()
	var cf := ConfigFile.new()
	if cf.load(SETTINGS_PATH) == OK:
		for k in out:
			out[k] = cf.get_value("settings", k, out[k])
		profile = clampi(cf.get_value("save", "profile", 1), 1, PROFILES)
	elif cf.load(LEGACY_PATH) == OK:
		for k in out:
			out[k] = cf.get_value("settings", k, out[k])
		if cf.get_value("settings", "sound", true) == false:
			out.master = 0.0
	return out


func save_settings(settings: Dictionary) -> void:
	var cf := ConfigFile.new()
	for k in settings:
		cf.set_value("settings", k, settings[k])
	cf.set_value("save", "profile", profile)
	cf.save(SETTINGS_PATH)


# ---------------------------------------------------------------- profile

## {stats: Dictionary, seen_charms: Array, seen_hexes: Array}
func load_profile(p: int = profile) -> Dictionary:
	var data := _load(_profile_path(p))
	if data.is_empty() and p == 1:
		data = _migrate_legacy()
	data.merge({"stats": {}, "seen_charms": [], "seen_hexes": []})
	return data


func save_profile(data: Dictionary) -> void:
	_queue(_profile_path(), var_to_bytes(data))


func _migrate_legacy() -> Dictionary:
	var cf := ConfigFile.new()
	if cf.load(LEGACY_PATH) != OK:
		return {}
	var stats := {}
	for k in cf.get_section_keys("stats") if cf.has_section("stats") else []:
		stats[k] = cf.get_value("stats", k)
	return {"stats": stats}


# ---------------------------------------------------------------- run

func has_run(p: int = profile) -> bool:
	var path := _run_path(p)
	_mutex.lock()
	var queued := _pending.has(path)
	var bytes = _pending[path][1] if queued else null
	_mutex.unlock()
	if queued:
		return bytes != null
	return FileAccess.file_exists(path)


func load_run(p: int = profile) -> Dictionary:
	return _load(_run_path(p))


## The newest version of a file: a queued snapshot if any, else the disk.
func _load(path: String) -> Dictionary:
	_mutex.lock()
	var job = _pending.get(path)
	_mutex.unlock()
	if job != null:
		return bytes_to_var(job[1]) if job[1] is PackedByteArray else {}
	_io.lock()
	var data := _read(path)
	_io.unlock()
	return data


func save_run(snapshot: Dictionary) -> void:
	_queue(_run_path(), var_to_bytes(snapshot))


func delete_run() -> void:
	_queue(_run_path(), null)


## Move an unreadable run out of the way (kept as run.bad for inspection).
func set_aside_run(p: int = profile) -> void:
	flush()
	var path := _run_path(p)
	_io.lock()
	if FileAccess.file_exists(path):
		var bad := _dir(p) + "/run.bad"
		if FileAccess.file_exists(bad):
			DirAccess.remove_absolute(bad)
		DirAccess.rename_absolute(path, bad)
	_io.unlock()


# ---------------------------------------------------------------- io

func _queue(path: String, bytes) -> void:
	_mutex.lock()
	_seq += 1
	_pending[path] = [_seq, bytes]
	_mutex.unlock()
	_sem.post()


## Write everything still pending, right now, on this thread.
func flush() -> void:
	_mutex.lock()
	var jobs := _pending.duplicate()
	_pending.clear()
	_mutex.unlock()
	for path in jobs:
		_commit(path, jobs[path])


func _worker() -> void:
	while true:
		_sem.wait()
		_mutex.lock()
		if _quit:
			_mutex.unlock()
			return
		var jobs := _pending.duplicate()
		_pending.clear()
		_mutex.unlock()
		for path in jobs:
			_commit(path, jobs[path])


## Write a queued snapshot unless a newer one for that file already landed.
func _commit(path: String, job: Array) -> void:
	_io.lock()
	if job[0] > _written.get(path, -1):
		_write(path, job[1])
		_written[path] = job[0]
	_io.unlock()


static func _write(path: String, bytes) -> void:
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	if bytes == null:
		DirAccess.remove_absolute(path)
		return
	var tmp := path + ".tmp"
	var f := FileAccess.open_compressed(tmp, FileAccess.WRITE, FileAccess.COMPRESSION_ZSTD)
	if f == null:
		push_warning("save failed: %s" % tmp)
		return
	f.store_32(MAGIC)
	f.store_32(VERSION)
	f.store_32(bytes.size())
	f.store_buffer(bytes)
	f.close()
	if FileAccess.file_exists(path):
		DirAccess.remove_absolute(path)
	DirAccess.rename_absolute(tmp, path)


static func _read(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var f := FileAccess.open_compressed(path, FileAccess.READ, FileAccess.COMPRESSION_ZSTD)
	if f == null or f.get_32() != MAGIC:
		return {}
	f.get_32()  # version, for future migrations
	var size := f.get_32()
	var data = bytes_to_var(f.get_buffer(size))
	return data if data is Dictionary else {}
