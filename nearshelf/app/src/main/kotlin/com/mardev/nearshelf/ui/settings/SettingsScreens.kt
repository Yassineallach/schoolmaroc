package com.mardev.nearshelf.ui.settings

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.provider.Settings
import androidx.annotation.DrawableRes
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import com.mardev.nearshelf.BuildConfig
import com.mardev.nearshelf.R
import com.mardev.nearshelf.ads.ConsentManager
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject

@HiltViewModel
class SettingsViewModel @Inject constructor(val consent: ConsentManager) : ViewModel()

@Composable
private fun BackBar(title: String, onBack: () -> Unit) = @OptIn(ExperimentalMaterial3Api::class) TopAppBar(
    title = { Text(title) },
    navigationIcon = { IconButton(onClick = onBack) { Icon(painterResource(R.drawable.ic_arrow_left), stringResource(R.string.cd_back)) } },
)

@Composable
fun SettingsScreen(
    onBack: () -> Unit,
    onLibraries: () -> Unit,
    onPreferences: () -> Unit,
    onPrivacy: () -> Unit,
    onLicences: () -> Unit,
    onAbout: () -> Unit,
    vm: SettingsViewModel = hiltViewModel(),
) {
    val context = LocalContext.current
    Scaffold(topBar = { BackBar(stringResource(R.string.settings_title), onBack) }) { padding ->
        LazyColumn(Modifier.fillMaxSize().padding(padding), contentPadding = PaddingValues(vertical = 8.dp)) {
            item { SettingRow(R.drawable.ic_library, stringResource(R.string.settings_libraries), stringResource(R.string.settings_libraries_sub), onLibraries) }
            item { SettingRow(R.drawable.ic_sliders, stringResource(R.string.prefs_title), stringResource(R.string.settings_prefs_sub), onPreferences) }
            item {
                SettingRow(R.drawable.ic_notifications, stringResource(R.string.settings_notifications), stringResource(R.string.settings_notifications_sub)) {
                    context.startActivity(
                        Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(Settings.EXTRA_APP_PACKAGE, context.packageName),
                    )
                }
            }
            item {
                SettingRow(R.drawable.ic_map_pin, stringResource(R.string.settings_permissions), stringResource(R.string.settings_permissions_sub)) {
                    context.startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.fromParts("package", context.packageName, null)))
                }
            }
            item { HorizontalDivider(Modifier.padding(vertical = 8.dp)) }
            if (vm.consent.privacyOptionsRequired) {
                item {
                    SettingRow(R.drawable.ic_privacy, stringResource(R.string.settings_privacy_options), stringResource(R.string.settings_privacy_options_sub)) {
                        (context as? Activity)?.let(vm.consent::showPrivacyOptions)
                    }
                }
            }
            item { SettingRow(R.drawable.ic_privacy, stringResource(R.string.settings_privacy_policy), null, onPrivacy) }
            item { SettingRow(R.drawable.ic_licenses, stringResource(R.string.settings_licences), null, onLicences) }
            item { SettingRow(R.drawable.ic_info, stringResource(R.string.settings_about), stringResource(R.string.settings_version, BuildConfig.VERSION_NAME), onAbout) }
        }
    }
}

@Composable
private fun SettingRow(@DrawableRes icon: Int, title: String, subtitle: String?, onClick: () -> Unit) {
    Row(
        Modifier.fillMaxWidth().heightIn(min = 56.dp).clickable(onClick = onClick).padding(horizontal = 16.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(painterResource(icon), null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(22.dp))
        Column(Modifier.weight(1f).padding(horizontal = 16.dp)) {
            Text(title, style = MaterialTheme.typography.bodyLarge)
            subtitle?.let { Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant) }
        }
        Icon(painterResource(R.drawable.ic_caret_right), null, tint = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.size(18.dp))
    }
}

@Composable
fun AboutScreen(onBack: () -> Unit) {
    Scaffold(topBar = { BackBar(stringResource(R.string.settings_about), onBack) }) { padding ->
        Column(Modifier.fillMaxSize().padding(padding).padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text(stringResource(R.string.app_name), style = MaterialTheme.typography.displaySmall, color = MaterialTheme.colorScheme.primary)
            Text(stringResource(R.string.tagline), style = MaterialTheme.typography.bodyLarge)
            Text(stringResource(R.string.settings_version, BuildConfig.VERSION_NAME), style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text(stringResource(R.string.about_body), style = MaterialTheme.typography.bodyMedium)
            Text(stringResource(R.string.about_not_affiliated), style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text(stringResource(R.string.about_trademarks), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

/** Renders assets/privacy.md (the same text as PRIVACY.md in the repository). */
@Composable
fun PrivacyScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    val lines = remember { context.assets.open("privacy.md").bufferedReader().readLines() }
    Scaffold(topBar = { BackBar(stringResource(R.string.settings_privacy_policy), onBack) }) { padding ->
        LazyColumn(Modifier.fillMaxSize().padding(padding), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(lines.filter { it.isNotBlank() }) { line ->
                when {
                    line.startsWith("# ") -> Text(line.removePrefix("# "), style = MaterialTheme.typography.headlineSmall, modifier = Modifier.semantics { heading() })
                    line.startsWith("## ") -> Text(line.removePrefix("## "), style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(top = 8.dp).semantics { heading() })
                    line.startsWith("- ") -> Text("•  " + line.removePrefix("- ").replace("**", ""), style = MaterialTheme.typography.bodyMedium)
                    else -> Text(line.replace("**", ""), style = MaterialTheme.typography.bodyMedium)
                }
            }
        }
    }
}

private data class Licence(val name: String, val licence: String, val asset: String? = null)

private val LICENCES = listOf(
    Licence("Cormorant Garamond font", "SIL Open Font License 1.1", "licenses/cormorant_garamond_OFL.txt"),
    Licence("Phosphor Icons", "MIT", "licenses/phosphor_MIT.txt"),
    Licence("Lightswind UI (Skeleton, CountUp, Badge, TopLoader designs)", "MIT", "licenses/lightswind_MIT.txt"),
    Licence("Android Jetpack (Compose, Room, WorkManager, Glance, DataStore, Navigation, CameraX)", "Apache License 2.0"),
    Licence("Kotlin, kotlinx.coroutines, kotlinx.serialization", "Apache License 2.0"),
    Licence("Dagger / Hilt", "Apache License 2.0"),
    Licence("OkHttp, Retrofit", "Apache License 2.0"),
    Licence("Coil", "Apache License 2.0"),
    Licence("jsoup", "MIT"),
    Licence("Google Mobile Ads SDK, User Messaging Platform, Play services location, ML Kit barcode scanning", "Google terms of service"),
    Licence("Book data from Open Library", "Open Library terms (openlibrary.org)"),
)

@Composable
fun LicencesScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    var open by rememberSaveable { mutableStateOf<String?>(null) }
    Scaffold(topBar = { BackBar(stringResource(R.string.settings_licences), onBack) }) { padding ->
        LazyColumn(Modifier.fillMaxSize().padding(padding), contentPadding = PaddingValues(vertical = 8.dp)) {
            items(LICENCES) { l ->
                Column(
                    Modifier.fillMaxWidth().heightIn(min = 56.dp)
                        .then(if (l.asset != null) Modifier.clickable { open = l.asset } else Modifier)
                        .padding(horizontal = 20.dp, vertical = 10.dp),
                ) {
                    Text(l.name, style = MaterialTheme.typography.bodyLarge)
                    Text(l.licence, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
    }
    open?.let { asset ->
        val text = remember(asset) { context.assets.open(asset).bufferedReader().readText() }
        AlertDialog(
            onDismissRequest = { open = null },
            confirmButton = { TextButton(onClick = { open = null }) { Text(stringResource(R.string.action_close)) } },
            text = { LazyColumn { item { Text(text, style = MaterialTheme.typography.bodySmall) } } },
        )
    }
}
