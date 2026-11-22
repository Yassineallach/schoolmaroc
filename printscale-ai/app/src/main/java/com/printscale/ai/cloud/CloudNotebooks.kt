package com.printscale.ai.cloud

import com.printscale.ai.BuildConfig

/**
 * Links to the AuraSR v2 server notebooks in the GitHub repo. Opening one hands off to the browser
 * (or the Colab/Kaggle app); the notebook then prints the link the app connects to.
 */
object CloudNotebooks {
    private const val PATH = "printscale-ai/notebooks"

    private fun github(file: String, repo: String, ref: String) = "https://github.com/$repo/blob/$ref/$PATH/$file"

    /** The server notebook: it starts AuraSR plus a tunnel and prints the link the app connects to. */
    fun colabUrl(repo: String = BuildConfig.NOTEBOOK_REPO, ref: String = BuildConfig.NOTEBOOK_REF) =
        "https://colab.research.google.com/github/$repo/blob/$ref/$PATH/PrintScale_Server_Colab.ipynb"

    /** Kaggle's documented "Open in Kaggle" import link. */
    fun kaggleUrl(repo: String = BuildConfig.NOTEBOOK_REPO, ref: String = BuildConfig.NOTEBOOK_REF) =
        "https://www.kaggle.com/kernels/welcome?src=" + github("PrintScale_Server_Kaggle.ipynb", repo, ref)
}
