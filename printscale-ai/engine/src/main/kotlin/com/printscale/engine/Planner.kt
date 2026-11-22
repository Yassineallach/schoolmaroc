package com.printscale.engine

import kotlin.math.max
import kotlin.math.min

/** What the device can spare for one job. Measured by the app before planning. */
data class DeviceBudget(
    val heapBytesAvailable: Long,
    val freeDiskBytes: Long,
)

data class PrintTarget(val size: PrintSize, val dpi: Int)

/**
 * The decision for one job: whether the AI model runs, what it produces, and how far
 * interpolation has to go from there to hit the exact target.
 */
data class UpscalePlan(
    val sourceW: Int,
    val sourceH: Int,
    val targetW: Int,
    val targetH: Int,
    val useAi: Boolean,
    /** Size the 4× model produces before the final resample (equals source when useAi is false). */
    val aiW: Int,
    val aiH: Int,
    val print: PrintTarget?,
    val estimatedPngBytes: Long,
    val warnings: List<String>,
    val blockers: List<String>,
) {
    val feasible: Boolean get() = blockers.isEmpty()

    /** Overall enlargement from the prepared artwork to the output file. */
    val effectiveScale: Double get() = max(targetW.toDouble() / sourceW, targetH.toDouble() / sourceH)

    /** > 1 means the output is larger than what the model produced and the rest is interpolated. */
    val interpolationBeyondAi: Double get() = max(targetW.toDouble() / aiW, targetH.toDouble() / aiH)

    /** Pixel density the AI-generated detail reaches at the chosen print size. */
    val aiDetailDpi: Double?
        get() = print?.let { min(aiW / it.size.widthIn, aiH / it.size.heightIn) }
}

object Planner {
    const val AI_SCALE = 4
    /** Largest prepared crop the on-device model is allowed to process (4096 × 4096). */
    const val MAX_SOURCE_PIXELS = 4096L * 4096L
    const val MAX_OUTPUT_SIDE = 20000
    const val MAX_OUTPUT_PIXELS = 250_000_000L
    /** Lossless PNG of upscaled artwork is usually 40 to 60 percent of raw size. Used only for space checks. */
    private const val PNG_RATIO = 0.55

    fun plan(
        sourceW: Int,
        sourceH: Int,
        targetW: Int,
        targetH: Int,
        hasAlpha: Boolean,
        budget: DeviceBudget,
        print: PrintTarget? = null,
    ): UpscalePlan {
        val warnings = mutableListOf<String>()
        val blockers = mutableListOf<String>()
        val srcPx = sourceW.toLong() * sourceH
        val outPx = targetW.toLong() * targetH
        val useAi = targetW > sourceW || targetH > sourceH
        val aiW = if (useAi) sourceW * AI_SCALE else sourceW
        val aiH = if (useAi) sourceH * AI_SCALE else sourceH
        val channels = if (hasAlpha) 4 else 3
        val pngBytes = (outPx * channels * PNG_RATIO).toLong()

        if (useAi && srcPx > MAX_SOURCE_PIXELS) {
            blockers += "The crop is ${mp(srcPx)} MP. The on-device model accepts up to ${mp(MAX_SOURCE_PIXELS)} MP. " +
                "Crop tighter, or choose a smaller output that needs no AI step."
        }
        if (targetW > MAX_OUTPUT_SIDE || targetH > MAX_OUTPUT_SIDE || outPx > MAX_OUTPUT_PIXELS) {
            blockers += "$targetW × $targetH px is beyond this app's limit of $MAX_OUTPUT_SIDE px per side " +
                "and ${MAX_OUTPUT_PIXELS / 1_000_000} MP. Choose a smaller size or a lower DPI."
        }
        // Java heap: the prepared source as ints (twice: buffer + bleed copy) plus one strip of AI rows.
        val heapNeed = srcPx * 8 + 64L * 1024 * 1024
        if (heapNeed > budget.heapBytesAvailable) {
            blockers += "Not enough free memory for a ${mp(srcPx)} MP crop on this device. Crop tighter or close other apps."
        }
        val diskNeed = pngBytes * 2 + 64L * 1024 * 1024
        if (diskNeed > budget.freeDiskBytes) {
            blockers += "About ${mb(diskNeed)} MB of free storage is needed and only ${mb(budget.freeDiskBytes)} MB is available."
        }

        val beyond = max(targetW.toDouble() / aiW, targetH.toDouble() / aiH)
        if (useAi && beyond > 1.02) {
            warnings += "The AI model produces $aiW × $aiH px (4×). Reaching $targetW × $targetH px needs another " +
                "${PrintMath.formatFactor(beyond)} of Lanczos interpolation, which adds pixels but not new detail."
        }
        if (!useAi) {
            warnings += "Your crop is already at least as large as the target. It will be resized with Lanczos " +
                "resampling only. No AI step runs."
        }
        if (useAi && srcPx > 4_000_000L) {
            warnings += "Large crop (${mp(srcPx)} MP). On a phone the AI step can take many minutes."
        }
        if (outPx > 100_000_000L) {
            warnings += "Very large output (${mp(outPx)} MP). Encoding and saving will take a while."
        }
        print?.let { p ->
            val aiDpi = min(aiW / p.size.widthIn, aiH / p.size.heightIn)
            if (aiDpi < p.dpi * 0.5) {
                warnings += "At this size the AI detail is about ${aiDpi.toInt()} DPI. The file will be ${p.dpi} DPI, " +
                    "but expect softness when viewed up close."
            }
        }
        return UpscalePlan(
            sourceW, sourceH, targetW, targetH, useAi, aiW, aiH, print, pngBytes, warnings, blockers,
        )
    }

    private fun mp(px: Long) = String.format("%.1f", px / 1_000_000.0)
    private fun mb(b: Long) = (b / (1024 * 1024)).toString()
}
