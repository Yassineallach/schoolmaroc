package com.mardev.nearshelf.core.provider.overdrive

import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.http.GET
import retrofit2.http.Path
import retrofit2.http.Query
import retrofit2.http.Url

/**
 * Both hosts are the public, unauthenticated endpoints the Libby web app uses.
 * Bodies come back raw so [OverDriveParser] owns all decoding (and fixtures can
 * be replayed through the same code).
 */
internal interface OverDriveApi {
    @GET
    suspend fun locate(@Url url: String): Response<ResponseBody>

    @GET("v2/libraries/{key}/media")
    suspend fun media(
        @Path("key") libraryKey: String,
        @Query("query") query: String,
        @Query("perPage") perPage: Int = 24,
    ): Response<ResponseBody>
}
