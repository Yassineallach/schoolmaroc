package com.printscale.engine

import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.FloatBuffer

/**
 * Real-ESRGAN ships two checkpoints of the same network: general-x4v3 (strong denoise) and
 * general-wdn-x4v3 (weak denoise). Its own "denoise strength" control linearly interpolates
 * their weights. Both ONNX files are exported from identical graphs, so the weights sit at the
 * same byte offsets; blend_map.json lists those ranges (produced by tools/export_realesrgan_onnx.py).
 */
object ModelBlender {
    fun parseRanges(json: String): List<IntArray> {
        val body = json.substringAfter("\"ranges\"").substringAfter('[').substringBeforeLast("]")
        return Regex("\\[(\\d+),\\s*(\\d+)\\]").findAll(body).map {
            intArrayOf(it.groupValues[1].toInt(), it.groupValues[2].toInt())
        }.toList()
    }

    /** strength 1 = general-x4v3 only, 0 = wdn only. */
    fun blend(strong: ByteArray, weak: ByteArray, ranges: List<IntArray>, strength: Float): ByteArray {
        require(strong.size == weak.size) { "Model files do not match" }
        val t = strength.coerceIn(0f, 1f)
        if (t >= 0.999f) return strong
        if (t <= 0.001f) return weak
        val out = strong.copyOf()
        val a = ByteBuffer.wrap(strong).order(ByteOrder.LITTLE_ENDIAN)
        val b = ByteBuffer.wrap(weak).order(ByteOrder.LITTLE_ENDIAN)
        val o = ByteBuffer.wrap(out).order(ByteOrder.LITTLE_ENDIAN)
        for (r in ranges) {
            val off = r[0]
            val len = r[1]
            require(off >= 0 && off + len <= strong.size && len % 4 == 0) { "Bad weight range" }
            var p = off
            while (p < off + len) {
                o.putFloat(p, t * a.getFloat(p) + (1 - t) * b.getFloat(p))
                p += 4
            }
        }
        return out
    }
}

/** Runs the exported Real-ESRGAN ONNX graph with ONNX Runtime on the CPU. */
class OrtSrModel(modelBytes: ByteArray, threads: Int) : SrModel {
    private val env: OrtEnvironment = OrtEnvironment.getEnvironment()
    private val session: OrtSession
    private val runOptions = OrtSession.RunOptions()
    override val scale: Int = 4

    init {
        val opts = OrtSession.SessionOptions().apply {
            setOptimizationLevel(OrtSession.SessionOptions.OptLevel.ALL_OPT)
            setIntraOpNumThreads(threads.coerceAtLeast(1))
        }
        session = env.createSession(modelBytes, opts)
        opts.close()
    }

    override fun run(chw: FloatArray, h: Int, w: Int): FloatArray {
        OnnxTensor.createTensor(env, FloatBuffer.wrap(chw), longArrayOf(1, 3, h.toLong(), w.toLong())).use { input ->
            session.run(mapOf("input" to input), runOptions).use { result ->
                val t = result.get(0) as OnnxTensor
                val fb = t.floatBuffer
                val outArr = FloatArray(fb.remaining())
                fb.get(outArr)
                return outArr
            }
        }
    }

    override fun interrupt() {
        runCatching { runOptions.setTerminate(true) }
    }

    override fun close() {
        session.close()
        runOptions.close()
    }
}
