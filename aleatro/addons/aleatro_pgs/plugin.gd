@tool
extends EditorPlugin

## Adds the AleatroPGS Android plugin (bin/aleatro_pgs.aar, built from
## res://android_plugin) and the Play Games Services SDK to Android exports.
## Android plugins need a Gradle build (Use Gradle Build in the preset).

const PGS_SDK := "com.google.android.gms:play-services-games-v2:22.1.0"

var _export: AndroidExport


func _enter_tree() -> void:
	_export = AndroidExport.new()
	add_export_plugin(_export)


func _exit_tree() -> void:
	remove_export_plugin(_export)
	_export = null


class AndroidExport extends EditorExportPlugin:
	func _get_name() -> String:
		return "AleatroPGS"

	func _supports_platform(platform: EditorExportPlatform) -> bool:
		return platform is EditorExportPlatformAndroid

	func _get_android_libraries(_platform: EditorExportPlatform, _debug: bool) -> PackedStringArray:
		return PackedStringArray(["aleatro_pgs/bin/aleatro_pgs.aar"])

	func _get_android_dependencies(_platform: EditorExportPlatform, _debug: bool) -> PackedStringArray:
		return PackedStringArray([PGS_SDK])
