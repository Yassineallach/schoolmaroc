package com.mardev.nearshelf.ui.scanner

import androidx.annotation.OptIn
import androidx.camera.core.ExperimentalGetImage
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import com.google.mlkit.vision.barcode.BarcodeScannerOptions
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.barcode.common.Barcode
import com.google.mlkit.vision.common.InputImage
import com.mardev.nearshelf.core.match.Isbn

/**
 * Feeds camera frames to ML Kit's bundled EAN-13 model. Reports the first valid
 * ISBN once; non-book EANs (groceries, price add-ons) are reported separately so
 * the screen can say "that's not a book barcode".
 */
class IsbnAnalyzer(
    private val onIsbn: (String) -> Unit,
    private val onOtherBarcode: () -> Unit,
) : ImageAnalysis.Analyzer {
    private val scanner = BarcodeScanning.getClient(
        BarcodeScannerOptions.Builder().setBarcodeFormats(Barcode.FORMAT_EAN_13).build(),
    )
    @Volatile private var done = false

    @OptIn(ExperimentalGetImage::class)
    override fun analyze(proxy: ImageProxy) {
        val media = proxy.image
        if (done || media == null) {
            proxy.close()
            return
        }
        scanner.process(InputImage.fromMediaImage(media, proxy.imageInfo.rotationDegrees))
            .addOnSuccessListener { codes ->
                if (done) return@addOnSuccessListener
                val isbn = codes.firstNotNullOfOrNull { c -> c.rawValue?.let(Isbn::fromBarcode) }
                when {
                    isbn != null -> { done = true; onIsbn(isbn) }
                    codes.isNotEmpty() -> onOtherBarcode()
                }
            }
            .addOnCompleteListener { proxy.close() }
    }

    fun close() = scanner.close()
}
