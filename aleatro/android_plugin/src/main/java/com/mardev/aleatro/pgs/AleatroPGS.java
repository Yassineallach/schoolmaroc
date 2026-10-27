package com.mardev.aleatro.pgs;

import android.app.Activity;
import android.content.Intent;
import android.util.Log;
import android.view.View;

import androidx.annotation.NonNull;

import com.google.android.gms.games.AuthenticationResult;
import com.google.android.gms.games.PlayGames;
import com.google.android.gms.games.PlayGamesSdk;
import com.google.android.gms.tasks.Task;

import org.godotengine.godot.Godot;
import org.godotengine.godot.plugin.GodotPlugin;
import org.godotengine.godot.plugin.SignalInfo;
import org.godotengine.godot.plugin.UsedByGodot;

import java.util.HashSet;
import java.util.Set;

/**
 * Play Games Services v2 for Aleatro: sign-in, achievements and leaderboards.
 * Reached from GDScript as Engine.get_singleton("AleatroPGS"). Every call is
 * fire and forget; results come back as signals.
 */
public class AleatroPGS extends GodotPlugin {
    private static final String TAG = "AleatroPGS";
    private static final int RC_UI = 9201;

    private static final SignalInfo SIGNED_IN = new SignalInfo("signed_in", Boolean.class);
    private static final SignalInfo PLAYER = new SignalInfo("player", String.class, String.class);
    private static final SignalInfo FAILED = new SignalInfo("failed", String.class, String.class);

    private boolean authenticated = false;

    public AleatroPGS(Godot godot) {
        super(godot);
    }

    @NonNull
    @Override
    public String getPluginName() {
        return "AleatroPGS";
    }

    @NonNull
    @Override
    public Set<SignalInfo> getPluginSignals() {
        Set<SignalInfo> signals = new HashSet<>();
        signals.add(SIGNED_IN);
        signals.add(PLAYER);
        signals.add(FAILED);
        return signals;
    }

    @Override
    public View onMainCreate(Activity activity) {
        PlayGamesSdk.initialize(activity);
        return null;
    }

    // ------------------------------------------------------------ sign-in

    /** Checks the automatic sign-in Play Games does at launch; emits signed_in. */
    @UsedByGodot
    public void check_sign_in() {
        Activity a = getActivity();
        if (a == null) return;
        a.runOnUiThread(() -> report(PlayGames.getGamesSignInClient(a).isAuthenticated(), "check_sign_in"));
    }

    /** Asks the player to sign in (after declining the automatic one); emits signed_in. */
    @UsedByGodot
    public void sign_in() {
        Activity a = getActivity();
        if (a == null) return;
        a.runOnUiThread(() -> report(PlayGames.getGamesSignInClient(a).signIn(), "sign_in"));
    }

    @UsedByGodot
    public boolean is_signed_in() {
        return authenticated;
    }

    private void report(Task<AuthenticationResult> task, String what) {
        task.addOnCompleteListener(t -> {
            authenticated = t.isSuccessful() && t.getResult().isAuthenticated();
            emitSignal(SIGNED_IN.getName(), authenticated);
            if (!t.isSuccessful()) fail(what, t.getException());
            if (authenticated) loadPlayer();
        });
    }

    private void loadPlayer() {
        Activity a = getActivity();
        if (a == null) return;
        PlayGames.getPlayersClient(a).getCurrentPlayer().addOnCompleteListener(t -> {
            if (t.isSuccessful() && t.getResult() != null) {
                emitSignal(PLAYER.getName(), t.getResult().getPlayerId(), t.getResult().getDisplayName());
            }
        });
    }

    // ------------------------------------------------------------ achievements

    @UsedByGodot
    public void unlock_achievement(String id) {
        Activity a = getActivity();
        if (a == null || !authenticated) return;
        PlayGames.getAchievementsClient(a).unlock(id);
    }

    /** For an incremental achievement: sets its progress to at least `steps`. */
    @UsedByGodot
    public void set_achievement_steps(String id, int steps) {
        Activity a = getActivity();
        if (a == null || !authenticated || steps <= 0) return;
        PlayGames.getAchievementsClient(a).setSteps(id, steps);
    }

    @UsedByGodot
    public void show_achievements() {
        Activity a = getActivity();
        if (a == null) return;
        PlayGames.getAchievementsClient(a).getAchievementsIntent()
                .addOnSuccessListener(i -> a.startActivityForResult(i, RC_UI))
                .addOnFailureListener(e -> fail("show_achievements", e));
    }

    // ------------------------------------------------------------ leaderboards

    @UsedByGodot
    public void submit_score(String id, long score) {
        Activity a = getActivity();
        if (a == null || !authenticated) return;
        PlayGames.getLeaderboardsClient(a).submitScore(id, score);
    }

    @UsedByGodot
    public void show_leaderboard(String id) {
        Activity a = getActivity();
        if (a == null) return;
        PlayGames.getLeaderboardsClient(a).getLeaderboardIntent(id)
                .addOnSuccessListener(i -> a.startActivityForResult(i, RC_UI))
                .addOnFailureListener(e -> fail("show_leaderboard", e));
    }

    @UsedByGodot
    public void show_all_leaderboards() {
        Activity a = getActivity();
        if (a == null) return;
        PlayGames.getLeaderboardsClient(a).getAllLeaderboardsIntent()
                .addOnSuccessListener(i -> a.startActivityForResult(i, RC_UI))
                .addOnFailureListener(e -> fail("show_all_leaderboards", e));
    }

    private void fail(String what, Exception e) {
        String msg = e == null ? "unknown" : String.valueOf(e.getMessage());
        Log.w(TAG, what + " failed: " + msg);
        emitSignal(FAILED.getName(), what, msg);
    }
}
