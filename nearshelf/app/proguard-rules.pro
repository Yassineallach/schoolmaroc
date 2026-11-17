# kotlinx.serialization: keep generated serializers for @Serializable classes.
-keepattributes *Annotation*, InnerClasses
-keepclassmembers @kotlinx.serialization.Serializable class ** {
    *** Companion;
    kotlinx.serialization.KSerializer serializer(...);
}
# Retrofit service interfaces are reflected on at runtime.
-keep,allowobfuscation interface com.mardev.nearshelf.core.provider.**.*Api
