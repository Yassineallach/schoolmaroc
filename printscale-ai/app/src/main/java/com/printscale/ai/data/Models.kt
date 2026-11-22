package com.printscale.ai.data

import com.printscale.engine.CropState
import com.printscale.engine.EnhanceSettings
import com.printscale.engine.FitMode
import com.printscale.engine.PrintSize
import com.printscale.engine.PrintTarget
import com.printscale.engine.Provenance
import org.json.JSONArray
import org.json.JSONObject

data class ImportedImage(
    val id: String,
    val displayName: String,
    val mime: String,
    val formatLabel: String,
    val fileSize: Long,
    /** Size after EXIF orientation. */
    val width: Int,
    val height: Int,
    /** Size the app decodes for processing (equal to width/height unless the image is huge). */
    val workW: Int,
    val workH: Int,
    val exifRotated: Boolean,
    val hasAlpha: Boolean,
    val colorSpaceName: String,
    val hasIcc: Boolean,
    /** Set when this artwork is an upscaled result, so print checks can tell real detail from added pixels. */
    val provenance: Provenance? = null,
) {
    val downscaledForWork: Boolean get() = workW != width || workH != height

    fun toJson(): JSONObject = JSONObject()
        .put("id", id).put("displayName", displayName).put("mime", mime).put("formatLabel", formatLabel)
        .put("fileSize", fileSize).put("width", width).put("height", height).put("workW", workW).put("workH", workH)
        .put("exifRotated", exifRotated).put("hasAlpha", hasAlpha).put("colorSpaceName", colorSpaceName)
        .put("hasIcc", hasIcc)
        .put("provenance", provenance?.let {
            JSONObject().put("originalW", it.originalW).put("originalH", it.originalH)
                .put("upscaledW", it.upscaledW).put("upscaledH", it.upscaledH).put("ai", it.aiUpscaled)
        } ?: JSONObject.NULL)

    companion object {
        fun fromJson(o: JSONObject) = ImportedImage(
            o.getString("id"), o.getString("displayName"), o.getString("mime"), o.getString("formatLabel"),
            o.getLong("fileSize"), o.getInt("width"), o.getInt("height"), o.getInt("workW"), o.getInt("workH"),
            o.getBoolean("exifRotated"), o.getBoolean("hasAlpha"), o.getString("colorSpaceName"), o.getBoolean("hasIcc"),
            o.optJSONObject("provenance")?.let {
                Provenance(it.getInt("originalW"), it.getInt("originalH"), it.getInt("upscaledW"), it.getInt("upscaledH"), it.getBoolean("ai"))
            },
        )
    }
}

/** Everything the background worker needs to reproduce what the editor showed. */
data class JobSpec(
    val importId: String,
    val crop: CropState,
    val aspect: Double?,
    val fitMode: FitMode,
    /** ARGB fill for Fit mode, or null for transparent. */
    val background: Int?,
    val targetW: Int,
    val targetH: Int,
    val useAi: Boolean,
    val print: PrintTarget?,
    val settings: EnhanceSettings,
    /** ENGINE_DEVICE (Real-ESRGAN on the phone) or ENGINE_CLOUD (AuraSR on the user's notebook server). */
    val engine: String = ENGINE_DEVICE,
) {
    fun toJson(): JSONObject = JSONObject()
        .put("engine", engine)
        .put("importId", importId)
        .put("quarter", crop.quarterTurns).put("straighten", crop.straightenDeg.toDouble())
        .put("zoom", crop.zoom.toDouble()).put("panX", crop.panX.toDouble()).put("panY", crop.panY.toDouble())
        .put("aspect", aspect ?: JSONObject.NULL)
        .put("fitMode", fitMode.name)
        .put("background", background ?: JSONObject.NULL)
        .put("targetW", targetW).put("targetH", targetH).put("useAi", useAi)
        .put("printW", print?.size?.widthIn ?: JSONObject.NULL)
        .put("printH", print?.size?.heightIn ?: JSONObject.NULL)
        .put("dpi", print?.dpi ?: JSONObject.NULL)
        .put("detail", settings.detail.toDouble()).put("sharpen", settings.sharpen.toDouble())
        .put("denoise", settings.denoise.toDouble())

    companion object {
        fun fromJson(o: JSONObject) = JobSpec(
            importId = o.getString("importId"),
            crop = CropState(
                o.getInt("quarter"), o.getDouble("straighten").toFloat(), o.getDouble("zoom").toFloat(),
                o.getDouble("panX").toFloat(), o.getDouble("panY").toFloat(),
            ),
            aspect = if (o.isNull("aspect")) null else o.getDouble("aspect"),
            fitMode = FitMode.valueOf(o.getString("fitMode")),
            background = if (o.isNull("background")) null else o.getInt("background"),
            targetW = o.getInt("targetW"), targetH = o.getInt("targetH"), useAi = o.getBoolean("useAi"),
            print = if (o.isNull("dpi")) null else PrintTarget(PrintSize(o.getDouble("printW"), o.getDouble("printH")), o.getInt("dpi")),
            settings = EnhanceSettings(
                o.getDouble("detail").toFloat(), o.getDouble("sharpen").toFloat(), o.getDouble("denoise").toFloat(),
            ),
            engine = o.optString("engine", ENGINE_DEVICE),
        )

        const val ENGINE_DEVICE = "device"
        const val ENGINE_CLOUD = "cloud"
    }
}

data class ExportRecord(
    val fileName: String,
    val format: String,
    val sizeBytes: Long,
    val location: String,
    val uri: String,
    val at: Long,
) {
    fun toJson(): JSONObject = JSONObject().put("fileName", fileName).put("format", format)
        .put("sizeBytes", sizeBytes).put("location", location).put("uri", uri).put("at", at)

    companion object {
        fun fromJson(o: JSONObject) = ExportRecord(
            o.getString("fileName"), o.getString("format"), o.getLong("sizeBytes"),
            o.getString("location"), o.getString("uri"), o.getLong("at"),
        )
    }
}

/** A finished job. Files live in filesDir/jobs/{id}/ until the user deletes them. */
data class HistoryItem(
    val id: String,
    val createdAt: Long,
    val displayName: String,
    val importId: String,
    val originalW: Int,
    val originalH: Int,
    val preparedW: Int,
    val preparedH: Int,
    val finalW: Int,
    val finalH: Int,
    val aiUsed: Boolean,
    val printWIn: Double?,
    val printHIn: Double?,
    val dpi: Int?,
    val hasAlpha: Boolean,
    val masterBytes: Long,
    val durationMs: Long,
    val exports: List<ExportRecord>,
    val engine: String = JobSpec.ENGINE_DEVICE,
) {
    val effectiveScale: Double get() = maxOf(finalW.toDouble() / preparedW, finalH.toDouble() / preparedH)

    fun toJson(): JSONObject = JSONObject()
        .put("id", id).put("createdAt", createdAt).put("displayName", displayName).put("importId", importId)
        .put("originalW", originalW).put("originalH", originalH).put("preparedW", preparedW).put("preparedH", preparedH)
        .put("finalW", finalW).put("finalH", finalH).put("aiUsed", aiUsed)
        .put("printWIn", printWIn ?: JSONObject.NULL).put("printHIn", printHIn ?: JSONObject.NULL)
        .put("dpi", dpi ?: JSONObject.NULL).put("hasAlpha", hasAlpha).put("masterBytes", masterBytes)
        .put("durationMs", durationMs)
        .put("engine", engine)
        .put("exports", JSONArray().also { a -> exports.forEach { a.put(it.toJson()) } })

    companion object {
        fun fromJson(o: JSONObject) = HistoryItem(
            o.getString("id"), o.getLong("createdAt"), o.getString("displayName"), o.getString("importId"),
            o.getInt("originalW"), o.getInt("originalH"), o.getInt("preparedW"), o.getInt("preparedH"),
            o.getInt("finalW"), o.getInt("finalH"), o.getBoolean("aiUsed"),
            if (o.isNull("printWIn")) null else o.getDouble("printWIn"),
            if (o.isNull("printHIn")) null else o.getDouble("printHIn"),
            if (o.isNull("dpi")) null else o.getInt("dpi"),
            o.getBoolean("hasAlpha"), o.getLong("masterBytes"), o.getLong("durationMs"),
            o.optJSONArray("exports")?.let { a -> (0 until a.length()).map { ExportRecord.fromJson(a.getJSONObject(it)) } } ?: emptyList(),
            o.optString("engine", JobSpec.ENGINE_DEVICE),
        )
    }
}
