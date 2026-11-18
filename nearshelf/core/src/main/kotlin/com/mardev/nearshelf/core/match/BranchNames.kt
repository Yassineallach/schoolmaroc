package com.mardev.nearshelf.core.match

/**
 * Branch names differ between sources: Libby says "Ballard", BiblioCommons "Ballard Branch",
 * a registry may say "Ballard Library". Compare them without those words.
 */
object BranchNames {
    private val noise = Regex("\\b(the|branch|library|public|neighbou?rhood|community|regional|centre|center)\\b")

    fun key(name: String): String =
        TextNormalizer.basic(name).replace(noise, " ").replace(Regex("\\s+"), " ").trim().ifEmpty { TextNormalizer.basic(name) }

    fun same(a: String, b: String): Boolean = key(a) == key(b)

    /**
     * [branch] names the branch [location] belongs to. Sierra reports shelf locations
     * like "Anderson Fiction" for the Anderson branch.
     */
    fun matches(branch: String, location: String): Boolean {
        val b = key(branch)
        val l = key(location)
        return b == l || (b.isNotEmpty() && l.startsWith("$b "))
    }
}
