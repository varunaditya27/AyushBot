package com.ayushbot.app.data.repository

import android.content.Context
import com.ayushbot.app.data.remote.BackendApi
import com.ayushbot.app.data.remote.model.ManifestResource
import java.io.File
import java.security.MessageDigest

data class ResourceUpdateResult(
    val resourceId: String,
    val version: Int,
    val applied: Boolean,
    val message: String,
)

class ResourceRepository(
    private val context: Context,
    private val api: BackendApi,
) {
    suspend fun fetchAndApplyUpdates(): Result<List<ResourceUpdateResult>> {
        return runCatching {
            val manifest = api.manifest()
            manifest.resources.map { resource ->
                downloadAndVerify(resource)
            }
        }
    }

    private suspend fun downloadAndVerify(resource: ManifestResource): ResourceUpdateResult {
        val response = api.downloadResource(resource.id)
        if (!response.isSuccessful) {
            return ResourceUpdateResult(
                resourceId = resource.resourceId,
                version = resource.version,
                applied = false,
                message = "Download failed with HTTP ${response.code()}",
            )
        }
        val body = response.body()
            ?: return ResourceUpdateResult(resource.resourceId, resource.version, false, "Empty body")
        val pending = File(resourceDir(), "${resource.id}.pending")
        val active = File(resourceDir(), "${resource.resourceId}-${resource.version}.bin")

        pending.outputStream().use { output ->
            body.byteStream().use { input -> input.copyTo(output) }
        }

        val checksum = sha256(pending)
        if (!checksum.equals(resource.sha256, ignoreCase = true)) {
            pending.delete()
            return ResourceUpdateResult(
                resourceId = resource.resourceId,
                version = resource.version,
                applied = false,
                message = "SHA-256 mismatch",
            )
        }

        if (active.exists()) {
            active.delete()
        }
        pending.renameTo(active)
        return ResourceUpdateResult(
            resourceId = resource.resourceId,
            version = resource.version,
            applied = true,
            message = "Applied",
        )
    }

    private fun resourceDir(): File {
        return File(context.filesDir, "sync_resources").also { it.mkdirs() }
    }

    private fun sha256(file: File): String {
        val digest = MessageDigest.getInstance("SHA-256")
        file.inputStream().use { input ->
            val buffer = ByteArray(DEFAULT_BUFFER_SIZE)
            while (true) {
                val read = input.read(buffer)
                if (read <= 0) break
                digest.update(buffer, 0, read)
            }
        }
        return digest.digest().joinToString("") { "%02x".format(it) }
    }
}
