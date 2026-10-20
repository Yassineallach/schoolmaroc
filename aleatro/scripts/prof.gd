class_name Prof
extends RefCounted

## Tiny section profiler for on-device numbers. Wrap hot code in
##   var t := Prof.begin()  ...  Prof.end("label", t)
## and read `Prof.rows()`. When `on` is false begin() returns 0 and end()
## returns at once, so the hooks cost next to nothing in normal play.

static var on := false
static var _calls := {}
static var _total := {}  # µs
static var _max := {}  # µs, slowest single run
static var _since := 0


static func begin() -> int:
	return Time.get_ticks_usec() if on else 0


static func end(label: String, started: int) -> void:
	if not on or started == 0:
		return
	var dt := Time.get_ticks_usec() - started
	_calls[label] = _calls.get(label, 0) + 1
	_total[label] = _total.get(label, 0) + dt
	_max[label] = maxi(_max.get(label, 0), dt)


static func reset() -> void:
	_calls.clear()
	_total.clear()
	_max.clear()
	_since = Time.get_ticks_usec()


static func start() -> void:
	reset()
	on = true


static func stop() -> void:
	on = false


## Up to `limit` rows, busiest first:
## [label, calls, total ms, avg ms, max ms, % of wall time since reset].
static func rows(limit := 10) -> Array:
	var wall := maxf((Time.get_ticks_usec() - _since) / 1000.0, 0.001)
	var labels := _total.keys()
	labels.sort_custom(func(a, b): return _total[a] > _total[b] or (_total[a] == _total[b] and _calls[a] > _calls[b]))
	var out: Array = []
	for l in labels.slice(0, limit):
		var tot: float = _total[l] / 1000.0
		out.append([l, _calls[l], tot, tot / _calls[l], _max[l] / 1000.0, 100.0 * tot / wall])
	return out


## The rows as a fixed-width text table, e.g. for a log.
static func report(limit := 10) -> String:
	var lines := ["%-22s %7s %9s %8s %8s %6s" % ["section", "calls", "total ms", "avg ms", "max ms", "%"]]
	for r in rows(limit):
		lines.append("%-22s %7d %9.2f %8.3f %8.3f %5.1f%%" % r)
	return "\n".join(lines)
