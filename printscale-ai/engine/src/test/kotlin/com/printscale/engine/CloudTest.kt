package com.printscale.engine

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Test
import java.awt.image.BufferedImage
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.File
import javax.imageio.ImageIO
import kotlin.random.Random

class CloudTest {
    private fun readAll(bytes: ByteArray): Triple<Int, Int, IntArray> {
        PngStreamReader(ByteArrayInputStream(bytes)).use { r ->
            val px = IntArray(r.width * r.height)
            val row = IntArray(r.width)
            for (y in 0 until r.height) { r.readRow(row); System.arraycopy(row, 0, px, y * r.width, r.width) }
            return Triple(r.width, r.height, px)
        }
    }

    @Test fun readerMatchesOwnWriter() {
        val rnd = Random(3)
        for (alpha in listOf(false, true)) {
            val w = 61; val h = 47
            // mix of noise and smooth ramps so every PNG filter type gets chosen somewhere
            val px = IntArray(w * h) { i ->
                val x = i % w; val y = i / w
                val a = if (alpha) (x * 4) and 0xFF else 255
                if (y % 3 == 0) (a shl 24) or (rnd.nextInt(1 shl 24)) else (a shl 24) or ((x * 4) shl 16) or ((y * 5) shl 8) or ((x + y) and 0xFF)
            }
            val bos = ByteArrayOutputStream()
            val wr = PngStreamWriter(bos, w, h, alpha, 300, null)
            for (y in 0 until h) wr.writeRow(y, px.copyOfRange(y * w, (y + 1) * w))
            wr.finish()
            val (rw, rh, got) = readAll(bos.toByteArray())
            assertEquals(w, rw); assertEquals(h, rh)
            for (i in px.indices) assertEquals("pixel $i", px[i], got[i])
        }
    }

    @Test fun readerMatchesJavaImageIo() {
        for (type in listOf(BufferedImage.TYPE_INT_RGB, BufferedImage.TYPE_INT_ARGB, BufferedImage.TYPE_BYTE_GRAY)) {
            val img = BufferedImage(40, 30, type)
            val rnd = Random(type)
            for (y in 0 until 30) for (x in 0 until 40) img.setRGB(x, y, (0xFF shl 24) or rnd.nextInt(1 shl 24))
            val bytes = ByteArrayOutputStream().also { ImageIO.write(img, "png", it) }.toByteArray()
            val (w, h, px) = readAll(bytes)
            assertEquals(40, w); assertEquals(30, h)
            for (y in 0 until 30) for (x in 0 until 40) {
                // getRGB gamma-converts grey images, so compare the stored sample for those
                val expected = if (type == BufferedImage.TYPE_BYTE_GRAY) {
                    val v = img.raster.getSample(x, y, 0); (0xFF shl 24) or (v shl 16) or (v shl 8) or v
                } else img.getRGB(x, y)
                assertEquals("type $type at $x,$y", expected, px[y * 40 + x])
            }
        }
    }

    @Test fun linkParsing() {
        val l = CloudLink.parse("  https://calm-river-12.trycloudflare.com/?key=AbCdEfGh123_-x  ")!!
        assertEquals("https://calm-river-12.trycloudflare.com", l.baseUrl)
        assertEquals("AbCdEfGh123_-x", l.key)
        assertEquals(l, CloudLink.parse(l.asText()))
        assertEquals(l, CloudLink.parse("https://calm-river-12.trycloudflare.com/connect?key=AbCdEfGh123_-x"))
        assertEquals(l, CloudLink.parse("printscale://connect?server=https%3A%2F%2Fcalm-river-12.trycloudflare.com&key=AbCdEfGh123_-x"))
        assertNull(CloudLink.parse("https://calm-river-12.trycloudflare.com/"))           // no key
        assertNull(CloudLink.parse("http://calm-river-12.trycloudflare.com/?key=AbCdEfGh123")) // plain http off-device
        assertNull(CloudLink.parse("not a link"))
        assertNotNull(CloudLink.parse("http://10.0.2.2:8765/?key=local-test-key"))     // emulator to host, for testing
    }

    /** Runs against a real server: PRINTSCALE_TEST_SERVER=http://localhost:8765/?key=... */
    @Test fun roundTripThroughRealServer() {
        val text = System.getProperty("cloudServer").orEmpty()
        assumeTrue("set PRINTSCALE_TEST_SERVER to run", text.isNotEmpty())
        val link = CloudLink.parse(text)!!
        val client = CloudClient(link)
        val info = client.health()
        println("server: ${info.model} on ${info.device} ${info.gpu}")
        assertEquals("AuraSR v2", info.model)

        // the app uploads its prepared crop (here: transparent artwork, alpha already bled)
        val src = ModelPipelineTest.artwork(72, 56, alpha = true)
        AlphaBleed.apply(src)
        val upload = File.createTempFile("upload", ".png")
        PngStreamWriter(upload.outputStream(), src.width, src.height, true, null, null).also { w ->
            for (y in 0 until src.height) w.writeRow(y, src.argb.copyOfRange(y * src.width, (y + 1) * src.width))
            w.finish()
        }
        var sent = 0L
        val id = client.submit(upload, { s, _ -> sent = s }, { false })
        assertEquals(upload.length(), sent)
        var job: CloudJob
        var polls = 0
        do { Thread.sleep(1000); job = client.status(id); polls++ } while (!job.finished && !job.failed && polls < 600)
        assertTrue("job ended as ${job.state}: ${job.error}", job.finished)
        assertTrue(job.total > 0 && job.done == job.total)

        val result = File.createTempFile("result", ".png")
        client.download(id, result, { _, _ -> }, { false })
        PngStreamReader(result.inputStream()).use { r ->
            assertEquals(src.width * 4, r.width); assertEquals(src.height * 4, r.height)
            assertTrue("alpha comes back", r.hasAlpha)
            // the app's own resizer consumes the stream straight into its PNG writer
            val out = ByteArrayOutputStream()
            val png = PngStreamWriter(out, 500, 389, true, 300, null)
            StreamingResizer(r.width, r.height, 500, 389).run(r::readRow, png, {})
            png.finish()
            val img = ImageIO.read(ByteArrayInputStream(out.toByteArray()))
            assertEquals(500, img.width)
            assertEquals(0, img.getRGB(0, 0) ushr 24) // transparent corner stays transparent
        }
        client.cancel(id) // deletes it on the server
        try { client.status(id); throw AssertionError("job should be gone") } catch (e: CloudException) { assertTrue(e.message!!.contains("Not found") || e.message!!.contains("No such job")) }

        // wrong key is refused with a clear message
        try { CloudClient(link.copy(key = "wrong-key-000")).health(); throw AssertionError("expected 401") }
        catch (e: CloudException) { assertTrue(e.message!!.contains("rejected the key")) }
    }

    @Test fun cancelStopsRunningJob() {
        val text = System.getProperty("cloudServer").orEmpty()
        assumeTrue(text.isNotEmpty())
        val client = CloudClient(CloudLink.parse(text)!!)
        val src = ModelPipelineTest.artwork(256, 256)
        val upload = File.createTempFile("upload", ".png")
        PngStreamWriter(upload.outputStream(), 256, 256, false, null, null).also { w ->
            for (y in 0 until 256) w.writeRow(y, src.argb.copyOfRange(y * 256, (y + 1) * 256)); w.finish()
        }
        val id = client.submit(upload, { _, _ -> }, { false })
        do { Thread.sleep(500) } while (client.status(id).state == "queued")
        client.cancel(id)
        Thread.sleep(1500)
        try { client.status(id); throw AssertionError("job should be gone after cancel") } catch (e: CloudException) { /* deleted */ }
    }
}
