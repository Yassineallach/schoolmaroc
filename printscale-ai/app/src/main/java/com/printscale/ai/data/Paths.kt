package com.printscale.ai.data

import android.content.Context
import java.io.File

/** On-device storage layout. Nothing here leaves the phone unless the user exports or shares it. */
class Paths(context: Context) {
    val imports = File(context.filesDir, "imports").apply { mkdirs() }
    val jobs = File(context.filesDir, "jobs").apply { mkdirs() }
    val exports = File(context.cacheDir, "exports").apply { mkdirs() }
    val historyFile = File(context.filesDir, "history.json")

    fun importDir(id: String) = File(imports, id)
    fun importOriginal(id: String) = File(importDir(id), "original")
    fun importMeta(id: String) = File(importDir(id), "meta.json")
    fun importIcc(id: String) = File(importDir(id), "profile.icc")
    fun importThumb(id: String) = File(importDir(id), "thumb.jpg")

    fun jobDir(id: String) = File(jobs, id).apply { mkdirs() }
    fun jobSpec(id: String) = File(jobDir(id), "spec.json")
    fun jobMaster(id: String) = File(jobDir(id), "master.png")
    fun jobPreview(id: String) = File(jobDir(id), "preview.png")
    fun jobBefore(id: String) = File(jobDir(id), "before.png")
    fun jobSource(id: String) = File(jobDir(id), "source.png")
}

fun File.sizeRecursive(): Long = if (isFile) length() else (listFiles()?.sumOf { it.sizeRecursive() } ?: 0L)
