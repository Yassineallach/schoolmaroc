package com.mardev.nearshelf.core.provider.overdrive

import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.testing.Fixtures
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

class OverDriveParserTest {

    @Test
    fun `locate collapses Toronto branches into one lending system`() {
        val libs = OverDriveParser.parseLibraries(Fixtures.read("overdrive/locate_toronto.json"))
        val toronto = libs.single { it.key == "toronto" }
        assertEquals("Toronto Public Library", toronto.name)
        assertEquals(ProviderId.OVERDRIVE, toronto.provider)
        assertEquals("CA", toronto.countryCode)
        assertEquals("https://libbyapp.com/library/toronto", toronto.catalogUrl)
        assertEquals(libs.size, libs.map { it.key }.toSet().size, "keys must be unique")
    }

    @Test
    fun `locate finds NYPL by fulfillmentId`() {
        val libs = OverDriveParser.parseLibraries(Fixtures.read("overdrive/locate_new_york_public.json"))
        val nypl = libs.single { it.key == "nypl" }
        assertEquals("New York Public Library", nypl.name)
        assertEquals("US", nypl.countryCode)
    }

    @Test
    fun `locate with no match returns empty list`() {
        assertTrue(OverDriveParser.parseLibraries(Fixtures.read("overdrive/locate_empty.json")).isEmpty())
    }

    @Test
    fun `NYPL Project Hail Mary ebook matches recorded availability`() {
        val holdings = OverDriveParser.parseMedia(Fixtures.read("overdrive/media_nypl_project_hail_mary.json"))
        assertEquals(14, holdings.size)

        val ebook = holdings.single { it.providerItemId == "5665700" }
        assertEquals(Format.EBOOK, ebook.format)
        assertEquals("Project Hail Mary", ebook.title)
        assertEquals(listOf("Andy Weir"), ebook.authors)
        assertEquals("en", ebook.language)
        assertEquals(250, ebook.owned)
        assertEquals(0, ebook.available)
        assertEquals(230, ebook.holds)
        assertEquals(13, ebook.waitDays)
        assertFalse(ebook.isAvailableNow)
        assertTrue("9780593135211" in ebook.isbns)
        assertTrue(ebook.coverUrl!!.startsWith("https://"))
    }

    @Test
    fun `Spanish audiobook keeps language and drops narrator from authors`() {
        val holdings = OverDriveParser.parseMedia(Fixtures.read("overdrive/media_nypl_project_hail_mary.json"))
        val es = holdings.single { it.providerItemId == "6268492" }
        assertEquals(Format.AUDIOBOOK, es.format)
        assertEquals("Proyecto Hail Mary", es.title)
        assertEquals("es", es.language)
        assertEquals(listOf("Andy Weir"), es.authors)
    }

    @Test
    fun `available title carries no wait estimate`() {
        val holdings = OverDriveParser.parseMedia(Fixtures.read("overdrive/media_nypl_project_hail_mary.json"))
        val summary = holdings.single { it.providerItemId == "6597161" }
        assertTrue(summary.isAvailableNow)
        assertEquals(2, summary.available)
        assertNull(summary.waitDays)
    }

    @Test
    fun `ISBN search returns the single edition`() {
        val holdings = OverDriveParser.parseMedia(Fixtures.read("overdrive/media_nypl_isbn_9780593135211.json"))
        assertEquals(listOf("5665700"), holdings.map { it.providerItemId })
    }

    @Test
    fun `unknown fields and missing optional fields are tolerated`() {
        val holdings = OverDriveParser.parseMedia(
            """{"items":[{"id":"1","title":"T","type":{"id":"magazine"},"brandNewField":true}]}""",
        )
        val h = holdings.single()
        assertEquals(Format.OTHER, h.format)
        assertNull(h.owned)
        assertTrue(h.authors.isEmpty())
    }
}
