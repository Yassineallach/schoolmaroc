package com.mardev.nearshelf.ui.components

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.widget.Toast
import androidx.core.net.toUri
import com.mardev.nearshelf.R

/** Opens a borrow/hold link: Libby's App Link opens the app if installed, else the browser. */
fun Context.openExternal(url: String) {
    val intent = Intent(Intent.ACTION_VIEW, url.toUri()).addCategory(Intent.CATEGORY_BROWSABLE)
    try {
        startActivity(intent)
    } catch (_: ActivityNotFoundException) {
        Toast.makeText(this, R.string.error_no_app_for_link, Toast.LENGTH_LONG).show()
    }
}
