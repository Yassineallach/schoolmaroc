package com.mardev.nearshelf.ui.scanner

import com.mardev.nearshelf.ui.theme.ButtonShape
import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.provider.Settings
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.compose.CameraXViewfinder
import androidx.camera.core.Camera
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.Preview
import androidx.camera.core.SurfaceRequest
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.lifecycle.awaitInstance
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.mardev.nearshelf.R
import com.mardev.nearshelf.ui.components.EmptyState
import kotlinx.coroutines.delay
import java.util.concurrent.Executors

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ScannerScreen(onBack: () -> Unit, onIsbn: (String) -> Unit, onTypeInstead: () -> Unit) {
    val context = LocalContext.current
    var granted by remember {
        mutableStateOf(ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED)
    }
    var askedOnce by remember { mutableStateOf(false) }
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) {
        granted = it
        askedOnce = true
    }
    LaunchedEffect(Unit) { if (!granted) launcher.launch(Manifest.permission.CAMERA) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.scanner_title)) },
                navigationIcon = {
                    IconButton(onClick = onBack) { Icon(painterResource(R.drawable.ic_arrow_left), stringResource(R.string.cd_back)) }
                },
            )
        },
    ) { padding ->
        if (granted) {
            CameraScanner(onIsbn, onTypeInstead, Modifier.padding(padding))
        } else if (askedOnce) {
            Column(Modifier.padding(padding)) {
                EmptyState(
                    icon = R.drawable.ic_camera,
                    title = stringResource(R.string.scanner_permission_title),
                    body = stringResource(R.string.scanner_permission_body),
                    action = stringResource(R.string.scanner_open_settings),
                    onAction = {
                        context.startActivity(
                            Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.fromParts("package", context.packageName, null)),
                        )
                    },
                )
                OutlinedButton(shape = ButtonShape, onClick = onTypeInstead, modifier = Modifier.align(Alignment.CenterHorizontally)) {
                    Text(stringResource(R.string.scanner_type_instead))
                }
            }
        }
    }
}

@Composable
private fun CameraScanner(onIsbn: (String) -> Unit, onTypeInstead: () -> Unit, modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val currentOnIsbn by rememberUpdatedState(onIsbn)
    var surfaceRequest by remember { mutableStateOf<SurfaceRequest?>(null) }
    var camera by remember { mutableStateOf<Camera?>(null) }
    var torchOn by remember { mutableStateOf(false) }
    var notABookAt by remember { mutableLongStateOf(0L) }
    var noCamera by remember { mutableStateOf(false) }

    val analyzer = remember {
        IsbnAnalyzer(
            onIsbn = { isbn -> ContextCompat.getMainExecutor(context).execute { currentOnIsbn(isbn) } },
            onOtherBarcode = { notABookAt = System.currentTimeMillis() },
        )
    }
    val executor = remember { Executors.newSingleThreadExecutor() }

    LaunchedEffect(lifecycleOwner) {
        val provider = ProcessCameraProvider.awaitInstance(context)
        val preview = Preview.Builder().build().apply { setSurfaceProvider { req -> surfaceRequest = req } }
        val analysis = ImageAnalysis.Builder()
            .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
            .build()
            .apply { setAnalyzer(executor, analyzer) }
        provider.unbindAll()
        camera = try {
            provider.bindToLifecycle(lifecycleOwner, CameraSelector.DEFAULT_BACK_CAMERA, preview, analysis)
        } catch (e: IllegalArgumentException) {
            noCamera = true // no back camera on this device
            null
        } catch (e: IllegalStateException) {
            noCamera = true
            null
        }
    }
    DisposableEffect(Unit) {
        onDispose {
            analyzer.close()
            executor.shutdown()
        }
    }

    var showNotABook by remember { mutableStateOf(false) }
    LaunchedEffect(notABookAt) {
        if (notABookAt == 0L) return@LaunchedEffect
        showNotABook = true
        delay(2500)
        showNotABook = false
    }

    if (noCamera) {
        Column(modifier) {
            EmptyState(R.drawable.ic_camera, stringResource(R.string.scanner_no_camera_title), stringResource(R.string.scanner_no_camera_body))
            OutlinedButton(shape = ButtonShape, onClick = onTypeInstead, modifier = Modifier.align(Alignment.CenterHorizontally)) {
                Text(stringResource(R.string.scanner_type_instead))
            }
        }
        return
    }
    Box(modifier.fillMaxSize().background(Color.Black)) {
        surfaceRequest?.let { CameraXViewfinder(surfaceRequest = it, modifier = Modifier.fillMaxSize()) }
        // Aiming frame shaped like a book barcode.
        Box(
            Modifier.align(Alignment.Center).fillMaxWidth(0.78f).aspectRatio(1.9f)
                .border(BorderStroke(3.dp, Color.White.copy(alpha = 0.9f)), RoundedCornerShape(16.dp)),
        )
        Column(
            Modifier.align(Alignment.BottomCenter).fillMaxWidth().padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Surface(shape = RoundedCornerShape(12.dp), color = Color.Black.copy(alpha = 0.6f), contentColor = Color.White) {
                Text(
                    stringResource(if (showNotABook) R.string.scanner_not_a_book else R.string.scanner_hint),
                    textAlign = TextAlign.Center,
                    style = MaterialTheme.typography.bodyLarge,
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 10.dp).semantics { liveRegion = LiveRegionMode.Polite },
                )
            }
            if (camera?.cameraInfo?.hasFlashUnit() == true) {
                Button(shape = ButtonShape, onClick = {
                    torchOn = !torchOn
                    camera?.cameraControl?.enableTorch(torchOn)
                }) {
                    Icon(painterResource(if (torchOn) R.drawable.ic_torch_off else R.drawable.ic_torch), null)
                    Text(stringResource(if (torchOn) R.string.scanner_torch_off else R.string.scanner_torch_on), Modifier.padding(start = 8.dp))
                }
            }
            OutlinedButton(shape = ButtonShape, onClick = onTypeInstead, colors = androidx.compose.material3.ButtonDefaults.outlinedButtonColors(contentColor = Color.White)) {
                Text(stringResource(R.string.scanner_type_instead))
            }
        }
    }
}
