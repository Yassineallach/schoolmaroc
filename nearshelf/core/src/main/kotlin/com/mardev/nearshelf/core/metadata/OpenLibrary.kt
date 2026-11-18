package com.mardev.nearshelf.core.metadata

import com.mardev.nearshelf.core.match.BookMatcher
import com.mardev.nearshelf.core.match.Isbn
import kotlinx.coroutines.CancellationException
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.HttpUrl
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.IOException

/** What Open Library knows about a work: every edition's ISBN, the edition's language, a cover. */
@Serializable
data class WorkInfo(
    val workKey: String,
    val title: String,
    val authors: List<String>,
    val isbns: Set<String>,
    /** ISO 639-1 language of the specific edition looked up, when known. */
    val language: String? = null,
    val coverUrl: String? = null,
)

@Serializable
internal data class OlEdition(
    val title: String? = null,
    val works: List<OlKey> = emptyList(),
    val languages: List<OlKey> = emptyList(),
    val covers: List<Long> = emptyList(),
)

@Serializable
internal data class OlKey(val key: String)

@Serializable
internal data class OlSearch(val docs: List<OlDoc> = emptyList())

@Serializable
internal data class OlDoc(
    val key: String,
    val title: String? = null,
    @kotlinx.serialization.SerialName("author_name") val authorName: List<String> = emptyList(),
    val isbn: List<String> = emptyList(),
    val language: List<String> = emptyList(),
    @kotlinx.serialization.SerialName("cover_i") val coverId: Long? = null,
)

/**
 * Open Library (free, no key). Two calls for an ISBN: the edition record (its own
 * language and title) and a work search that lists every ISBN of every edition.
 * Never throws for network trouble: metadata is a nice-to-have, so failures return null.
 */
class OpenLibrary(
    private val client: OkHttpClient,
    private val baseUrl: String = "https://openlibrary.org",
) {
    private val json = Json { ignoreUnknownKeys = true; coerceInputValues = true }
    private val fields = "key,title,author_name,isbn,language,cover_i"

    suspend fun byIsbn(isbn: String): WorkInfo? {
        val clean = Isbn.normalize(isbn)
        val edition = get("$baseUrl/isbn/$clean.json".toHttpUrl())?.let { parseEdition(it) }
        val search = get(
            "$baseUrl/search.json".toHttpUrl().newBuilder()
                .addQueryParameter("isbn", clean)
                .addQueryParameter("fields", fields)
                .addQueryParameter("limit", "1")
                .build(),
        )?.let { parseSearch(it) }
        val doc = search?.docs?.firstOrNull()
        if (edition == null && doc == null) return null
        return merge(clean, edition, doc)
    }

    /** Best work for a title (and author); null unless its title really matches. */
    suspend fun byTitle(title: String, author: String?): WorkInfo? {
        val url = "$baseUrl/search.json".toHttpUrl().newBuilder()
            .addQueryParameter("title", title)
            .apply { if (!author.isNullOrBlank()) addQueryParameter("author", author) }
            .addQueryParameter("fields", fields)
            .addQueryParameter("limit", "5")
            .build()
        val doc = get(url)?.let { parseSearch(it) }?.docs
            ?.firstOrNull { it.title != null && BookMatcher.titlesMatch(title, it.title) }
            ?: return null
        return toWork(doc, language = null)
    }

    internal fun parseEdition(body: String): OlEdition? = runCatching { json.decodeFromString<OlEdition>(body) }.getOrNull()
    internal fun parseSearch(body: String): OlSearch? = runCatching { json.decodeFromString<OlSearch>(body) }.getOrNull()

    internal fun merge(isbn: String, edition: OlEdition?, doc: OlDoc?): WorkInfo {
        val language = LanguageCodes.toIso1(edition?.languages?.firstOrNull()?.key)
        val base = doc?.let { toWork(it, language) }
        val cover = edition?.covers?.firstOrNull { it > 0 }?.let(::coverUrl) ?: base?.coverUrl
        return WorkInfo(
            workKey = base?.workKey ?: edition?.works?.firstOrNull()?.key.orEmpty(),
            title = edition?.title ?: base?.title.orEmpty(),
            authors = base?.authors.orEmpty(),
            isbns = (base?.isbns.orEmpty() + isbn),
            language = language,
            coverUrl = cover,
        )
    }

    private fun toWork(doc: OlDoc, language: String?) = WorkInfo(
        workKey = doc.key,
        title = doc.title.orEmpty(),
        authors = doc.authorName,
        isbns = doc.isbn.map(Isbn::normalize).filter { it.length == 13 }.toSet(),
        language = language,
        coverUrl = doc.coverId?.let(::coverUrl),
    )

    private fun coverUrl(id: Long) = "https://covers.openlibrary.org/b/id/$id-M.jpg"

    private fun get(url: HttpUrl): String? = try {
        client.newCall(Request.Builder().url(url).build()).execute().use { r ->
            if (r.isSuccessful) r.body.string() else null
        }
    } catch (e: CancellationException) {
        throw e
    } catch (_: IOException) {
        null
    }
}
