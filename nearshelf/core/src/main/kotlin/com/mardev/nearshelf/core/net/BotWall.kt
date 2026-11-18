package com.mardev.nearshelf.core.net

/**
 * Recognises a bot check instead of real content. Nearshelf never tries to get
 * past one: the user is offered the catalog's own page in their browser instead.
 * Patterns are from real responses (the Koha fixtures ending in _429.html and _bot_challenge.html).
 */
object BotWall {
    fun isWall(code: Int, body: String): Boolean {
        val head = body.take(20_000)
        return (code == 429 || code == 403 || code == 503) && ("cloudflare" in head.lowercase() || "Too Many Requests" in head) ||
            "fast_challenge/" in head || // Koha (Catalyst) and Aspen: /opac-tmpl/lib/koha_fast_challenge/, /files/fast_challenge/
            "<title>Just a moment...</title>" in head ||
            "Attention Required! | Cloudflare" in head ||
            "cf-chl-" in head
    }
}
