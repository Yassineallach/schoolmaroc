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
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
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
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import com.mardev.nearshelf.BuildConfig
import com.mardev.nearshelf.R
import com.mardev.nearshelf.ads.ConsentManager
import com.mardev.nearshelf.ui.components.NearshelfTopBar
import com.mardev.nearshelf.ui.components.SectionHeader
import com.mardev.nearshelf.ui.components.readableWidth
import com.mardev.nearshelf.ui.theme.Gutter
import com.mardev.nearshelf.ui.theme.Space
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject

@HiltViewModel
class SettingsViewModel @Inject constructor(val consent: ConsentManager) : ViewModel()

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
    SettingsContent(
        privacyOptionsRequired = vm.consent.privacyOptionsRequired,
        onBack = onBack,
        onLibraries = onLibraries,
        onPreferences = onPreferences,
        onNotifications = {
            context.startActivity(Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(Settings.EXTRA_APP_PACKAGE, context.packageName))
        },
        onPermissions = {
            context.startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.fromParts("package", context.packageName, null)))
        },
        onPrivacyOptions = { (context as? Activity)?.let(vm.consent::showPrivacyOptions) },
        onPrivacy = onPrivacy,
        onLicences = onLicences,
        onAbout = onAbout,
    )
}

/** Stateless Settings UI (rendered in the screenshot tests): two groups of plain rows. */
@Composable
internal fun SettingsContent(
    privacyOptionsRequired: Boolean,
    onBack: () -> Unit,
    onLibraries: () -> Unit,
    onPreferences: () -> Unit,
    onNotifications: () -> Unit,
    onPermissions: () -> Unit,
    onPrivacyOptions: () -> Unit,
    onPrivacy: () -> Unit,
    onLicences: () -> Unit,
    onAbout: () -> Unit,
) {
    Scaffold(
        topBar = { NearshelfTopBar(stringResource(R.string.settings_title), onBack = onBack) },
        containerColor = MaterialTheme.colorScheme.background,
    ) { padding ->
        LazyColumn(Modifier.fillMaxSize().padding(padding).readableWidth(), contentPadding = PaddingValues(bottom = Space.xl)) {
            item { SectionHeader(stringResource(R.string.settings_group_setup)) }
            item { SettingRow(R.drawable.ic_library, stringResource(R.string.settings_libraries), stringResource(R.string.settings_libraries_sub), onLibraries) }
            item { SettingRow(R.drawable.ic_sliders, stringResource(R.string.prefs_title), stringResource(R.string.settings_prefs_sub), onPreferences) }
            item { SettingRow(R.drawable.ic_notifications, stringResource(R.string.settings_notifications), stringResource(R.string.settings_notifications_sub), onNotifications) }
            item { SettingRow(R.drawable.ic_map_pin, stringResource(R.string.settings_permissions), stringResource(R.string.settings_permissions_sub), onPermissions, divider = false) }
            item { SectionHeader(stringResource(R.string.settings_group_about), Modifier.padding(top = Space.l)) }
            if (privacyOptionsRequired) {
                item { SettingRow(R.drawable.ic_privacy, stringResource(R.string.settings_privacy_options), stringResource(R.string.settings_privacy_options_sub), onPrivacyOptions) }
            }
            item { SettingRow(R.drawable.ic_privacy, stringResource(R.string.settings_privacy_policy), null, onPrivacy) }
            item { SettingRow(R.drawable.ic_licenses, stringResource(R.string.settings_licences), null, onLicences) }
            item { SettingRow(R.drawable.ic_info, stringResource(R.string.settings_about), stringResource(R.string.settings_version, BuildConfig.VERSION_NAME), onAbout, divider = false) }
        }
    }
}

/** Icon in the accent's secondary tone, title, one line of help, chevron; hairline below. */
@Composable
private fun SettingRow(@DrawableRes icon: Int, title: String, subtitle: String?, onClick: () -> Unit, divider: Boolean = true) {
    Column {
        Row(
            Modifier.fillMaxWidth().heightIn(min = 64.dp).clickable(role = Role.Button, onClick = onClick).padding(horizontal = Gutter, vertical = Space.m),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(painterResource(icon), null, tint = MaterialTheme.colorScheme.secondary, modifier = Modifier.size(22.dp))
            Spacer(Modifier.width(Space.l + 2.dp))
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text(title, style = MaterialTheme.typography.titleMedium)
                subtitle?.let { Text(it, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant) }
            }
            Icon(painterResource(R.drawable.ic_caret_right), null, tint = MaterialTheme.colorScheme.outline, modifier = Modifier.size(18.dp))
        }
        if (divider) HorizontalDivider(Modifier.padding(start = Gutter + 40.dp, end = Gutter), color = MaterialTheme.colorScheme.outlineVariant)
    }
}

/** The wordmark large once, then what Nearshelf is and isn't, in reading type. */
@Composable
fun AboutScreen(onBack: () -> Unit) {
    Scaffold(
        topBar = { NearshelfTopBar(stringResource(R.string.settings_about), onBack = onBack) },
        containerColor = MaterialTheme.colorScheme.background,
    ) { padding ->
        Column(
            Modifier.fillMaxSize().padding(padding).verticalScroll(rememberScrollState()).readableWidth()
                .padding(start = Gutter, end = Gutter, top = Space.l, bottom = Space.xxl),
        ) {
            Text(stringResource(R.string.app_name), style = MaterialTheme.typography.displaySmall, color = MaterialTheme.colorScheme.primary)
            Text(stringResource(R.string.tagline), style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(top = Space.xs))
            Text(
                stringResource(R.string.settings_version, BuildConfig.VERSION_NAME),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = Space.s),
            )
            HorizontalDivider(Modifier.padding(vertical = Space.xl), color = MaterialTheme.colorScheme.outlineVariant)
            Text(stringResource(R.string.about_body), style = MaterialTheme.typography.bodyLarge)
            Text(
                stringResource(R.string.about_not_affiliated),
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = Space.l),
            )
            Text(
                stringResource(R.string.about_trademarks),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = Space.xl),
            )
        }
    }
}

/** Renders assets/privacy.md (the same text as PRIVACY.md in the repository) as a readable page. */
@Composable
fun PrivacyScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    val lines = remember { context.assets.open("privacy.md").bufferedReader().readLines() }
    PrivacyContent(lines, onBack)
}

@Composable
internal fun PrivacyContent(lines: List<String>, onBack: () -> Unit) {
    Scaffold(
        topBar = { NearshelfTopBar(stringResource(R.string.settings_privacy_policy), onBack = onBack) },
        containerColor = MaterialTheme.colorScheme.background,
    ) { padding ->
        LazyColumn(
            Modifier.fillMaxSize().padding(padding).readableWidth(),
            contentPadding = PaddingValues(start = Gutter, end = Gutter, top = Space.s, bottom = Space.xxl),
            verticalArrangement = Arrangement.spacedBy(Space.s),
        ) {
            items(lines.filter { it.isNotBlank() }) { line ->
                when {
                    line.startsWith("# ") -> Text(line.removePrefix("# "), style = MaterialTheme.typography.headlineSmall, modifier = Modifier.semantics { heading() })
                    line.startsWith("## ") -> Text(line.removePrefix("## "), style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(top = Space.l).semantics { heading() })
                    line.startsWith("- ") -> Row {
                        // Hanging indent: wrapped lines align with the text, not the bullet.
                        Text("•", style = MaterialTheme.typography.bodyLarge, color = MaterialTheme.colorScheme.secondary, modifier = Modifier.width(Space.l))
                        Text(line.removePrefix("- ").replace("**", ""), style = MaterialTheme.typography.bodyLarge, modifier = Modifier.weight(1f))
                    }
                    else -> Text(line.replace("**", ""), style = MaterialTheme.typography.bodyLarge)
                }
            }
        }
    }
}

private data class Licence(val name: String, val licence: String, val asset: String? = null)

private val LICENCES = listOf(
    Licence("Newsreader font", "SIL Open Font License 1.1", "licenses/newsreader_OFL.txt"),
    Licence("Instrument Sans font", "SIL Open Font License 1.1", "licenses/instrument_sans_OFL.txt"),
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
    Scaffold(
        topBar = { NearshelfTopBar(stringResource(R.string.settings_licences), onBack = onBack) },
        containerColor = MaterialTheme.colorScheme.background,
    ) { padding ->
        LazyColumn(Modifier.fillMaxSize().padding(padding).readableWidth(), contentPadding = PaddingValues(bottom = Space.xl)) {
            itemsIndexed(LICENCES) { i, l ->
                Row(
                    Modifier.fillMaxWidth().heightIn(min = 64.dp)
                        .then(if (l.asset != null) Modifier.clickable(role = Role.Button) { open = l.asset } else Modifier)
                        .padding(horizontal = Gutter, vertical = Space.m),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        Text(l.name, style = MaterialTheme.typography.titleMedium)
                        Text(l.licence, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                    if (l.asset != null) {
                        Icon(painterResource(R.drawable.ic_caret_right), null, tint = MaterialTheme.colorScheme.outline, modifier = Modifier.size(18.dp))
                    }
                }
                if (i < LICENCES.lastIndex) HorizontalDivider(Modifier.padding(horizontal = Gutter), color = MaterialTheme.colorScheme.outlineVariant)
            }
        }
    }
    open?.let { asset ->
        val text = remember(asset) { context.assets.open(asset).bufferedReader().readText() }
        AlertDialog(
            onDismissRequest = { open = null },
            confirmButton = { TextButton(onClick = { open = null }) { Text(stringResource(R.string.action_close), style = MaterialTheme.typography.labelLarge) } },
            containerColor = MaterialTheme.colorScheme.background,
            shape = MaterialTheme.shapes.large,
            text = { LazyColumn { item { Text(text, style = MaterialTheme.typography.bodySmall) } } },
        )
    }
}
