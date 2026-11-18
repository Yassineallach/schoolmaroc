package com.mardev.nearshelf.ui.onboarding

import com.mardev.nearshelf.ui.theme.ButtonShape
import android.Manifest
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.annotation.DrawableRes
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.mardev.nearshelf.R
import kotlinx.coroutines.launch

/** First launch only: what Nearshelf does, add libraries, optional permissions. Every step can be skipped. */
@Composable
fun OnboardingScreen(onAddLibrary: () -> Unit, onDone: () -> Unit) {
    val pager = rememberPagerState { 3 }
    val scope = rememberCoroutineScope()
    var locationAsked by rememberSaveable { mutableStateOf(false) }
    var notificationsAsked by rememberSaveable { mutableStateOf(false) }
    val location = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { locationAsked = true }
    val notifications = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { notificationsAsked = true }
    val pageText = stringResource(R.string.onboarding_page, pager.currentPage + 1, 3)

    // Own surface, so text and background follow the theme wherever the screen is hosted.
    Surface(Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
        Column(Modifier.fillMaxSize().statusBarsPadding().navigationBarsPadding()) {
            Row(Modifier.fillMaxWidth().padding(8.dp)) {
                Spacer(Modifier.weight(1f))
                TextButton(onClick = onDone) { Text(stringResource(R.string.onboarding_skip)) }
            }
            HorizontalPager(pager, Modifier.weight(1f)) { page ->
                when (page) {
                    0 -> Page(R.drawable.ic_books, stringResource(R.string.onboarding_1_title), stringResource(R.string.onboarding_1_body))
                    1 -> Page(R.drawable.ic_library, stringResource(R.string.onboarding_2_title), stringResource(R.string.onboarding_2_body)) {
                        Button(shape = ButtonShape, onClick = onAddLibrary, modifier = Modifier.heightIn(min = 48.dp)) { Text(stringResource(R.string.libraries_add)) }
                    }
                    else -> Page(R.drawable.ic_map_pin, stringResource(R.string.onboarding_3_title), stringResource(R.string.onboarding_3_body)) {
                        OutlinedButton(shape = ButtonShape, 
                            onClick = { location.launch(Manifest.permission.ACCESS_COARSE_LOCATION) },
                            enabled = !locationAsked,
                            modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp),
                        ) { Text(stringResource(R.string.onboarding_allow_location)) }
                        if (Build.VERSION.SDK_INT >= 33) {
                            OutlinedButton(shape = ButtonShape, 
                                onClick = { notifications.launch(Manifest.permission.POST_NOTIFICATIONS) },
                                enabled = !notificationsAsked,
                                modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp),
                            ) { Text(stringResource(R.string.onboarding_allow_notifications)) }
                        }
                        Text(stringResource(R.string.onboarding_3_later), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant, textAlign = TextAlign.Center)
                    }
                }
            }
            Row(
                Modifier.fillMaxWidth().padding(20.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Row(Modifier.weight(1f).semantics(mergeDescendants = true) { contentDescription = pageText }, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    repeat(3) { i ->
                        Box(
                            Modifier.size(if (i == pager.currentPage) 10.dp else 8.dp).clip(CircleShape)
                                .background(if (i == pager.currentPage) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.outlineVariant),
                        )
                    }
                }
                if (pager.currentPage < 2) {
                    Button(shape = ButtonShape, onClick = { scope.launch { pager.animateScrollToPage(pager.currentPage + 1) } }, modifier = Modifier.heightIn(min = 48.dp)) {
                        Text(stringResource(R.string.onboarding_next))
                    }
                } else {
                    Button(shape = ButtonShape, onClick = onDone, modifier = Modifier.heightIn(min = 48.dp)) { Text(stringResource(R.string.onboarding_done)) }
                }
            }
        }
    }
}

@Composable
private fun Page(@DrawableRes icon: Int, title: String, body: String, actions: @Composable () -> Unit = {}) {
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 28.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(16.dp, Alignment.CenterVertically),
    ) {
        Icon(painterResource(icon), null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(64.dp))
        Text(title, style = MaterialTheme.typography.displaySmall, textAlign = TextAlign.Center, modifier = Modifier.semantics { heading() })
        Text(body, style = MaterialTheme.typography.bodyLarge, color = MaterialTheme.colorScheme.onSurfaceVariant, textAlign = TextAlign.Center, modifier = Modifier.widthIn(max = 420.dp))
        Column(Modifier.widthIn(max = 360.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(10.dp)) { actions() }
    }
}
