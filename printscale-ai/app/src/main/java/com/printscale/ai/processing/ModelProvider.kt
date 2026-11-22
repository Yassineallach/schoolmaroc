package com.printscale.ai.processing

import android.content.Context
import com.printscale.engine.ModelBlender
import com.printscale.engine.OrtSrModel

/** Loads the bundled Real-ESRGAN checkpoints and builds a session for one denoise strength. */
object ModelProvider {
    const val MODEL_NAME = "Real-ESRGAN General x4v3"

    fun create(context: Context, denoise: Float): OrtSrModel {
        val assets = context.assets
        val strong = assets.open("models/realesr-general-x4v3.onnx").use { it.readBytes() }
        val weak = assets.open("models/realesr-general-wdn-x4v3.onnx").use { it.readBytes() }
        val ranges = ModelBlender.parseRanges(assets.open("models/blend_map.json").use { it.readBytes().decodeToString() })
        val bytes = ModelBlender.blend(strong, weak, ranges, denoise)
        // Four threads: enough to use the big cores without the little cores holding up each tile.
        val threads = Runtime.getRuntime().availableProcessors().coerceIn(1, 4)
        return OrtSrModel(bytes, threads)
    }
}
