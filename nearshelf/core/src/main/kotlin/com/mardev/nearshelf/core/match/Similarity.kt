package com.mardev.nearshelf.core.match

import kotlin.math.max
import kotlin.math.min

object Similarity {

    fun jaroWinkler(s: String, t: String): Double {
        if (s == t) return 1.0
        if (s.isEmpty() || t.isEmpty()) return 0.0
        val window = max(0, max(s.length, t.length) / 2 - 1)
        val sMatch = BooleanArray(s.length)
        val tMatch = BooleanArray(t.length)
        var matches = 0
        for (i in s.indices) {
            for (j in max(0, i - window) until min(t.length, i + window + 1)) {
                if (tMatch[j] || s[i] != t[j]) continue
                sMatch[i] = true; tMatch[j] = true; matches++; break
            }
        }
        if (matches == 0) return 0.0
        var k = 0
        var transpositions = 0
        for (i in s.indices) {
            if (!sMatch[i]) continue
            while (!tMatch[k]) k++
            if (s[i] != t[k]) transpositions++
            k++
        }
        val m = matches.toDouble()
        val jaro = (m / s.length + m / t.length + (m - transpositions / 2.0) / m) / 3.0
        var prefix = 0
        while (prefix < min(4, min(s.length, t.length)) && s[prefix] == t[prefix]) prefix++
        return jaro + prefix * 0.1 * (1 - jaro)
    }

    /** 1 − editDistance / longerLength. */
    fun levenshteinRatio(s: String, t: String): Double {
        if (s == t) return 1.0
        val longer = max(s.length, t.length)
        if (longer == 0) return 1.0
        var prev = IntArray(t.length + 1) { it }
        var cur = IntArray(t.length + 1)
        for (i in 1..s.length) {
            cur[0] = i
            for (j in 1..t.length) {
                val cost = if (s[i - 1] == t[j - 1]) 0 else 1
                cur[j] = minOf(cur[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost)
            }
            val tmp = prev; prev = cur; cur = tmp
        }
        return 1.0 - prev[t.length].toDouble() / longer
    }
}
