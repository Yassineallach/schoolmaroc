package com.mardev.nearshelf.core.match

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class IsbnAndSimilarityTest {
    @Test
    fun isbn10to13() = assertEquals("9780593135204", Isbn.to13("0593135202"))

    @Test
    fun isbnValidation() {
        assertTrue(Isbn.isValid("978-0-593-13520-4"))
        assertTrue(Isbn.isValid("080442957X"))
        assertFalse(Isbn.isValid("9780593135205"))
        assertFalse(Isbn.isValid("12345"))
    }

    @Test
    fun similarityBounds() {
        assertEquals(1.0, Similarity.jaroWinkler("abc", "abc"))
        assertEquals(0.0, Similarity.jaroWinkler("", "abc"))
        assertEquals(0.75, Similarity.levenshteinRatio("abcd", "abce"))
        assertTrue(Similarity.jaroWinkler("project hail mary", "proyecto hail mary") > 0.95)
    }

    @Test
    fun normalizer() {
        assertEquals("project hail mary", TextNormalizer.title("Project Hail Mary: A Novel"))
        assertEquals("weir", TextNormalizer.surname("Weir, Andy"))
        assertEquals("garcia marquez", TextNormalizer.title("García Márquez"))
        assertEquals("enders game", TextNormalizer.title("Ender’s Game"))
    }
}
