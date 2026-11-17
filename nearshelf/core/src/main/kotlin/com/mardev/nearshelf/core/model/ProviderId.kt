package com.mardev.nearshelf.core.model

enum class ProviderId(val displayName: String, val kind: Kind) {
    OVERDRIVE("Libby", Kind.DIGITAL),
    HOOPLA("Hoopla", Kind.DIGITAL),
    BIBLIOCOMMONS("BiblioCommons", Kind.PHYSICAL),
    KOHA("Koha", Kind.PHYSICAL),
    EVERGREEN("Evergreen", Kind.PHYSICAL),
    ASPEN("Aspen Discovery", Kind.PHYSICAL),
    POLARIS("Polaris", Kind.PHYSICAL),
    SIERRA_ENCORE("Sierra", Kind.PHYSICAL),
    SIERRA_VEGA("Vega", Kind.PHYSICAL);

    enum class Kind { DIGITAL, PHYSICAL }
}
