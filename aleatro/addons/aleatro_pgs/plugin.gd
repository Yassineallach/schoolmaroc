@tool
extends EditorPlugin

## Adds the Aleatro Android plugins (bin/aleatro_pgs.aar, built from
## res://android_plugin: Play Games, and AdMob with consent and billing) and
## their SDKs to Android exports, and writes the AdMob app ID from
## res://ads/ads.cfg into the manifest. Android plugins need a Gradle build
## (Use Gradle Build in the preset).

const SDKS := [
	"com.google.android.gms:play-services-games-v2:22.1.0",
	"com.google.android.gms:play-services-ads:25.4.0",
	"com.google.android.ump:user-messaging-platform:3.2.0",
	"com.android.billingclient:billing:8.3.0",
]
const ADS_CONFIG := "res://ads/ads.cfg"
## Google's sample app ID: serves test ads only
const TEST_APP_ID := "ca-app-pub-3940256099942544~3347511713"

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
		return PackedStringArray(SDKS)

	func _get_android_manifest_application_element_contents(_platform: EditorExportPlatform, _debug: bool) -> String:
		var cf := ConfigFile.new()
		var app_id: String = TEST_APP_ID
		if cf.load(ADS_CONFIG) == OK and String(cf.get_value("admob", "app_id", "")).contains("~"):
			app_id = cf.get_value("admob", "app_id")
		# the Ads SDK stops the app at launch without this
		return '<meta-data android:name="com.google.android.gms.ads.APPLICATION_ID" android:value="%s"/>' % app_id
