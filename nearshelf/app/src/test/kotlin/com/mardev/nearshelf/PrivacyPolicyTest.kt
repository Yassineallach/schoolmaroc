package com.mardev.nearshelf

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

class PrivacyPolicyTest {
    @Test
    fun inAppPolicyMatchesRepositoryCopy() {
        val repo = File("../PRIVACY.md").readText()
        assertEquals("app/src/main/assets/privacy.md must equal PRIVACY.md", repo, File("src/main/assets/privacy.md").readText())
        assertTrue("not affiliated" in repo.lowercase())
    }
}
