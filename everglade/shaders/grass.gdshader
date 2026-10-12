// Meadow grass: thousands of thin curved blades per square metre.
//  * each blade takes its colour from the painted ground under its root
//    (meadow_base) so the carpet melts into the terrain with no seam
//  * dark, ground-tinted roots fading to sunlit, slightly warmer tips
//  * rolling wind gusts that sweep across the meadow in visible waves
//  * animals part the grass as they walk through it ("pushers")
//  * soft wrapped lighting on a mostly-up normal (a lush carpet, not noisy
//    individual blades), translucent tips against the sun and a gentle sheen
//  * blades sink into the ground with distance, where the matching terrain
//    colour takes over
shader_type spatial;
render_mode cull_disabled, world_vertex_coords;

#include "res://shaders/meadow.gdshaderinc"

global uniform float wind_strength;
global uniform float snow_amount;

uniform vec4 pushers[8];
uniform int pusher_count = 0;

varying vec3 v_col;
varying vec3 v_n;
varying float v_t;

void vertex() {
	float t = COLOR.g;            // 0 at the root .. 1 at the tip
	float rnd = COLOR.r;          // per-blade random
	vec3 root = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	vec3 base = VERTEX;
	float up = max(VERTEX.y - root.y, 0.0);
	float cam_d = length(CAMERA_POSITION_WORLD - root);
	// thin, crisp blades up close; fuller further away (no shimmering)
	vec3 side = (MODEL_MATRIX * vec4(UV2.x, 0.0, UV2.y, 0.0)).xyz;
	VERTEX += side * UV.x * (mix(0.45, 1.5, smoothstep(2.0, 22.0, cam_d)) - 1.0);
	// blades shrink into the ground far away (terrain colour takes over)
	float keep = 1.0 - smoothstep(GRASS_FADE_START, GRASS_FADE_END, cam_d);
	up *= keep;
	VERTEX.y = root.y + up;
	// --- wind: big slow gusts rolling across the meadow + per-blade flutter
	vec2 wdir = normalize(vec2(1.0, 0.35));
	float gust = noise(root.xz * 0.15 - wdir * TIME * 0.8);
	float wave = sin(dot(root.xz, wdir) * 0.55 - TIME * 2.0 + gust * 3.0) * 0.5 + 0.5;
	float bend = (0.18 + gust * wave * 0.95) * wind_strength;
	vec2 sway = wdir * bend + vec2(sin(TIME * 3.7 + rnd * 40.0), cos(TIME * 3.1 + rnd * 23.0)) * 0.06;
	// --- animals walking through push the blades apart and flatten them
	float flatten = 0.0;
	for (int i = 0; i < pusher_count; i++) {
		vec2 d = root.xz - pushers[i].xz;
		float l = length(d);
		float k = 1.0 - smoothstep(pushers[i].w * 0.35, pushers[i].w, l);
		sway += (d / max(l, 0.001)) * k * 1.6;
		flatten = max(flatten, k);
	}
	float tt = t * t;
	vec2 disp = sway * tt * up * 1.15;
	VERTEX.xz += disp;
	// keep the blade length roughly constant as it bends
	VERTEX.y -= (length(disp) * 0.45 + flatten * up * 0.35) * t;
	// --- colour from the ground beneath
	vec3 g = meadow_base(root.xz, root.y);
	g *= 0.86 + rnd * 0.28;
	// a few sun-bleached and a few deep-green blades
	g = mix(g, g * vec3(1.18, 1.1, 0.72), step(0.86, rnd) * 0.6);
	g = mix(g, g * vec3(0.78, 0.92, 0.82), step(rnd, 0.1) * 0.6);
	// roots match the ground exactly (no visible gaps between clumps), with
	// just a whisper of occlusion at the very base; tips lift brighter and
	// a little more saturated
	vec3 ground = meadow_base(root.xz, root.y);
	vec3 rootc = ground * GRASS_ROOT_SHADE;
	vec3 tipc = g * vec3(0.94, 1.1, 0.86);
	tipc = mix(vec3(dot(tipc, vec3(0.3, 0.59, 0.11))), tipc, 1.15);
	v_col = mix(rootc, tipc, smoothstep(0.08, 1.0, t));
	v_col = mix(v_col, vec3(0.92, 0.95, 1.0), snow_amount * smoothstep(0.3, 1.0, t) * 0.9);
	v_t = t;
	// mostly-up normal: the carpet shades softly like the ground it grows from
	v_n = normalize(mix(NORMAL, vec3(0.0, 1.0, 0.0), 0.55));
}

void fragment() {
	ALBEDO = v_col;
	NORMAL = normalize((VIEW_MATRIX * vec4(v_n, 0.0)).xyz);
	ROUGHNESS = 0.8;
	SPECULAR = 0.0; // no sky reflection: it bleaches thin blades
	BACKLIGHT = v_col * v_t;
}

void light() {
	float ndl = dot(NORMAL, LIGHT);
	float wrap = clamp((ndl + 0.45) / 1.45, 0.0, 1.0);
	float shadow = smoothstep(0.2, 0.6, ATTENUATION);
	vec3 lc = LIGHT_COLOR / PI;
	DIFFUSE_LIGHT += lc * mix(0.32, 1.0, smoothstep(0.1, 0.85, wrap)) * shadow;
	// sunlight glowing through the tips when looking toward the sun
	float through = pow(clamp(dot(VIEW, -LIGHT), 0.0, 1.0), 3.0);
	DIFFUSE_LIGHT += lc * BACKLIGHT / max(ALBEDO, vec3(0.05)) * through * 0.35 * shadow;
	// soft satin sheen across the blade tops
	float sh = pow(max(dot(NORMAL, normalize(LIGHT + VIEW)), 0.0), 20.0);
	SPECULAR_LIGHT += lc * ALBEDO * sh * 0.25 * shadow;
}
