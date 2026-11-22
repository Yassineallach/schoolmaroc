package com.printscale.ai.processing

import android.content.Context
import androidx.work.Data
import androidx.work.ExistingWorkPolicy
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkInfo
import androidx.work.WorkManager
import androidx.work.workDataOf
import com.printscale.ai.data.JobSpec
import com.printscale.ai.data.Paths
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.withContext
import java.util.UUID

enum class JobStage(val label: String) {
    QUEUED("Waiting to start"),
    PREPARING("Preparing image"),
    ANALYZING("Analyzing artwork"),
    UPSCALING("Enhancing details and upscaling"),
    FINALIZING("Preparing print output"),
}

sealed interface JobStatus {
    data class Running(val stage: JobStage, val done: Long, val total: Long, val etaMs: Long?, val startedAt: Long) : JobStatus
    data object Succeeded : JobStatus
    data class Failed(val message: String) : JobStatus
    data object Cancelled : JobStatus
    data object Missing : JobStatus
}

class ProcessingController(private val context: Context) {
    private val wm get() = WorkManager.getInstance(context)
    private val paths = Paths(context)

    suspend fun enqueue(spec: JobSpec): String = withContext(Dispatchers.IO) {
        val id = UUID.randomUUID()
        paths.jobSpec(id.toString()).writeText(spec.toJson().toString())
        val req = OneTimeWorkRequestBuilder<UpscaleWorker>()
            .setId(id)
            .setInputData(workDataOf(UpscaleWorker.KEY_JOB to id.toString()))
            .addTag(TAG)
            .build()
        // One job at a time: a phone has one set of CPU cores to give the model.
        wm.enqueueUniqueWork(UNIQUE, ExistingWorkPolicy.APPEND_OR_REPLACE, req)
        id.toString()
    }

    fun cancel(jobId: String) {
        wm.cancelWorkById(UUID.fromString(jobId))
    }

    fun observe(jobId: String): Flow<JobStatus> =
        wm.getWorkInfoByIdFlow(UUID.fromString(jobId)).map { it.toStatus() }

    /** Unfinished jobs, so Home can point back to one still running. */
    fun active(): Flow<List<String>> = wm.getWorkInfosByTagFlow(TAG).map { list ->
        list.filter { !it.state.isFinished }.map { it.id.toString() }
    }

    private fun WorkInfo?.toStatus(): JobStatus {
        if (this == null) return JobStatus.Missing
        return when (state) {
            WorkInfo.State.ENQUEUED, WorkInfo.State.BLOCKED -> JobStatus.Running(JobStage.QUEUED, 0, 0, null, 0)
            WorkInfo.State.RUNNING -> progress.toRunning()
            WorkInfo.State.SUCCEEDED -> JobStatus.Succeeded
            WorkInfo.State.FAILED -> JobStatus.Failed(outputData.getString(UpscaleWorker.KEY_ERROR) ?: "Processing failed.")
            WorkInfo.State.CANCELLED -> JobStatus.Cancelled
        }
    }

    private fun Data.toRunning(): JobStatus.Running {
        val stage = getString(UpscaleWorker.KEY_STAGE)?.let { runCatching { JobStage.valueOf(it) }.getOrNull() } ?: JobStage.PREPARING
        val eta = getLong(UpscaleWorker.KEY_ETA, -1L).takeIf { it >= 0 }
        return JobStatus.Running(stage, getLong(UpscaleWorker.KEY_DONE, 0), getLong(UpscaleWorker.KEY_TOTAL, 0), eta,
            getLong(UpscaleWorker.KEY_STARTED, 0))
    }

    companion object {
        const val TAG = "upscale"
        const val UNIQUE = "upscale-queue"
    }
}
