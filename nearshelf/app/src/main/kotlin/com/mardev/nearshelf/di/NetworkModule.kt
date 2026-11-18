package com.mardev.nearshelf.di

import com.mardev.nearshelf.BuildConfig
import com.mardev.nearshelf.core.match.BookMatcher
import com.mardev.nearshelf.core.metadata.OpenLibrary
import com.mardev.nearshelf.core.metadata.QueryExpander
import com.mardev.nearshelf.core.share.OkHttpPageFetcher
import com.mardev.nearshelf.core.share.PageFetcher
import com.mardev.nearshelf.data.RegistryRepository
import com.mardev.nearshelf.core.share.ShareParser
import com.mardev.nearshelf.core.net.NearshelfHttp
import com.mardev.nearshelf.core.provider.CatalogProvider
import com.mardev.nearshelf.core.provider.hoopla.HooplaProvider
import com.mardev.nearshelf.core.provider.overdrive.OverDriveProvider
import com.mardev.nearshelf.core.search.LibrarySearchService
import com.mardev.nearshelf.core.search.SearchCoordinator
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import dagger.multibindings.IntoSet
import okhttp3.OkHttpClient
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    @Provides
    @Singleton
    fun okHttp(): OkHttpClient = NearshelfHttp.client(BuildConfig.VERSION_NAME)

    @Provides
    @Singleton
    fun overDrive(client: OkHttpClient): OverDriveProvider = OverDriveProvider(client)

    @Provides
    @IntoSet
    fun overDriveAsProvider(p: OverDriveProvider): CatalogProvider = p

    @Provides
    @Singleton
    fun hoopla(client: OkHttpClient): HooplaProvider = HooplaProvider(client)

    @Provides
    @IntoSet
    fun hooplaAsProvider(p: HooplaProvider): CatalogProvider = p

    @Provides
    @Singleton
    fun librarySearch(providers: Set<@JvmSuppressWildcards CatalogProvider>, registry: RegistryRepository) =
        LibrarySearchService(providers.sortedBy { it.id.ordinal }) { registry.current }

    @Provides
    @Singleton
    fun searchCoordinator(providers: Set<@JvmSuppressWildcards CatalogProvider>) =
        SearchCoordinator(providers, BookMatcher())

    @Provides
    @Singleton
    fun openLibrary(client: OkHttpClient) = OpenLibrary(client)

    @Provides
    @Singleton
    fun queryExpander(ol: OpenLibrary) = QueryExpander(ol)

    @Provides
    @Singleton
    fun pageFetcher(client: OkHttpClient): PageFetcher = OkHttpPageFetcher(client)

    @Provides
    @Singleton
    fun shareParser(fetcher: PageFetcher) = ShareParser(fetcher)
}
