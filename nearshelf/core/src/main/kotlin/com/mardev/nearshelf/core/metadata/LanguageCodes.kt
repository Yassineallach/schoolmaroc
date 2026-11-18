package com.mardev.nearshelf.core.metadata

import java.util.Locale
import java.util.MissingResourceException

/** Converts MARC / ISO 639-2 codes ("eng", "fre", "spa") and English names ("English") to ISO 639-1 ("en"). */
object LanguageCodes {
    // ISO 639-2/B bibliographic codes that differ from the /T codes Java knows.
    private val bibliographic = mapOf(
        "fre" to "fr", "ger" to "de", "dut" to "nl", "chi" to "zh", "cze" to "cs", "gre" to "el",
        "per" to "fa", "rum" to "ro", "slo" to "sk", "wel" to "cy", "arm" to "hy", "baq" to "eu",
        "bur" to "my", "geo" to "ka", "ice" to "is", "mac" to "mk", "mao" to "mi", "may" to "ms",
        "alb" to "sq", "tib" to "bo",
    )

    private val byIso3: Map<String, String> by lazy {
        Locale.getISOLanguages().mapNotNull { two ->
            try {
                Locale.forLanguageTag(two).isO3Language.takeIf { it.isNotEmpty() }?.let { it to two }
            } catch (_: MissingResourceException) {
                null
            }
        }.toMap()
    }

    private val byEnglishName: Map<String, String> by lazy {
        Locale.getISOLanguages().associateBy { Locale.forLanguageTag(it).getDisplayLanguage(Locale.ENGLISH).lowercase() }
    }

    fun toIso1(code: String?): String? {
        val c = code?.trim()?.lowercase()?.removePrefix("/languages/") ?: return null
        return when {
            c.isEmpty() -> null
            c.length == 2 -> c
            c.length == 3 -> bibliographic[c] ?: byIso3[c]
            else -> byEnglishName[c.substringBefore(';').trim()]
        }
    }
}
