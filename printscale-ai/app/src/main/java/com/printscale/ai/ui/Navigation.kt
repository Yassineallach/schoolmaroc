package com.printscale.ai.ui

import androidx.compose.foundation.background
import androidx.compose.runtime.Composable
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.printscale.ai.AppGraph
import com.printscale.ai.ui.editor.EditorScreen
import com.printscale.ai.ui.history.HistoryScreen
import com.printscale.ai.ui.home.HomeScreen
import com.printscale.ai.ui.processing.ProcessingScreen
import com.printscale.ai.ui.result.ExportDoneScreen
import com.printscale.ai.ui.result.ResultScreen
import com.printscale.ai.ui.settings.SettingsScreen
import com.printscale.ai.ui.prep.PrepTab
import com.printscale.ai.ui.prep.PrintPrepScreen
import com.printscale.engine.PrintMethod

object Routes {
    const val HOME = "home"
    const val HISTORY = "history"
    const val SETTINGS = "settings"
    fun editor(importId: String, preset: String? = null, factor: Int? = null) =
        "editor/$importId?preset=${preset ?: ""}&factor=${factor ?: 0}"
    fun processing(jobId: String) = "processing/$jobId"
    fun prep(importId: String, method: PrintMethod, tab: PrepTab = PrepTab.PRINT) = "prep/$importId?method=${method.name}&tab=${tab.name}"
    fun result(jobId: String) = "result/$jobId"
    fun exported(jobId: String) = "exported/$jobId"
}

@Composable
fun AppNavHost(graph: AppGraph) {
    val nav = rememberNavController()
    NavHost(nav, startDestination = Routes.HOME,
        modifier = androidx.compose.ui.Modifier.background(androidx.compose.material3.MaterialTheme.colorScheme.background)) {
        composable(Routes.HOME) {
            HomeScreen(
                graph = graph,
                openEditor = { id, preset, factor -> nav.navigate(Routes.editor(id, preset, factor)) },
                openPrep = { id, method, tab -> nav.navigate(Routes.prep(id, method, tab)) },
                openResult = { nav.navigate(Routes.result(it)) },
                openProcessing = { nav.navigate(Routes.processing(it)) },
                openHistory = { nav.navigate(Routes.HISTORY) },
                openSettings = { nav.navigate(Routes.SETTINGS) },
            )
        }
        composable(
            "editor/{importId}?preset={preset}&factor={factor}",
            arguments = listOf(
                navArgument("importId") { type = NavType.StringType },
                navArgument("preset") { type = NavType.StringType; defaultValue = "" },
                navArgument("factor") { type = NavType.IntType; defaultValue = 0 },
            ),
        ) { e ->
            val args = e.arguments!!
            EditorScreen(
                graph = graph,
                importId = args.getString("importId")!!,
                initialPreset = args.getString("preset")?.takeIf { it.isNotEmpty() },
                initialFactor = args.getInt("factor").takeIf { it > 0 },
                onBack = { nav.popBackStack() },
                onStarted = { jobId -> nav.navigate(Routes.processing(jobId)) },
            )
        }
        composable(
            "prep/{importId}?method={method}&tab={tab}",
            arguments = listOf(
                navArgument("importId") { type = NavType.StringType },
                navArgument("method") { type = NavType.StringType; defaultValue = PrintMethod.DTF.name },
                navArgument("tab") { type = NavType.StringType; defaultValue = PrepTab.PRINT.name },
            ),
        ) { e ->
            val a = e.arguments!!
            PrintPrepScreen(
                graph = graph,
                importId = a.getString("importId")!!,
                method = runCatching { PrintMethod.valueOf(a.getString("method")!!) }.getOrDefault(PrintMethod.DTF),
                tab = runCatching { PrepTab.valueOf(a.getString("tab")!!) }.getOrDefault(PrepTab.PRINT),
                onBack = { nav.popBackStack() },
                onUpscale = { id -> nav.navigate(Routes.editor(id, factor = 4)) },
            )
        }
        composable("processing/{jobId}") { e ->
            val jobId = e.arguments!!.getString("jobId")!!
            ProcessingScreen(
                graph = graph, jobId = jobId,
                onDone = { nav.navigate(Routes.result(jobId)) { popUpTo("processing/{jobId}") { inclusive = true } } },
                onLeave = { nav.popBackStack() },
            )
        }
        composable("result/{jobId}") { e ->
            val jobId = e.arguments!!.getString("jobId")!!
            ResultScreen(
                graph = graph, jobId = jobId,
                onClose = { nav.popBackStack(Routes.HOME, inclusive = false) },
                onUpscaleAgain = { importId ->
                    // Return to the editor that started this job, or open a fresh one from history.
                    if (!nav.popBackStack("editor/{importId}?preset={preset}&factor={factor}", inclusive = false)) {
                        nav.navigate(Routes.editor(importId))
                    }
                },
                onExported = { nav.navigate(Routes.exported(jobId)) },
                onPrep = { importId -> nav.navigate(Routes.prep(importId, PrintMethod.DTF)) },
            )
        }
        composable("exported/{jobId}") { e ->
            val jobId = e.arguments!!.getString("jobId")!!
            ExportDoneScreen(graph = graph, jobId = jobId, onDone = { nav.popBackStack(Routes.HOME, inclusive = false) },
                onBack = { nav.popBackStack() })
        }
        composable(Routes.HISTORY) {
            HistoryScreen(graph = graph, onBack = { nav.popBackStack() }, openResult = { nav.navigate(Routes.result(it)) })
        }
        composable(Routes.SETTINGS) {
            SettingsScreen(graph = graph, onBack = { nav.popBackStack() })
        }
    }
}
