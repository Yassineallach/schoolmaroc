package com.mardev.nearshelf.di

import com.mardev.nearshelf.BuildConfig
import com.mardev.nearshelf.core.net.NearshelfHttp
import com.mardev.nearshelf.core.provider.CatalogProvider
import com.mardev.nearshelf.core.provider.overdrive.OverDriveProvider
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
}
