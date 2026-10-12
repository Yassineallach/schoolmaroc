// Meadow terrain: lush grass, painted paths (mask R = dirt, G = cobble,
// B = trodden ground around structures), sandy pond banks and seasonal snow.
shader_type spatial;
render_mode diffuse_lambert_wrap;

#include "res://shaders/toon.gdshaderinc"
#include "res://shaders/materials.gdshaderinc"
#include "res://shaders/meadow.gdshaderinc"
global uniform float snow_amount;

uniform sampler2D mask_tex : filter_linear, repeat_disable;
uniform float terrain_origin = -32.0;
uniform float terrain_size = 64.0;
uniform float water_level = -0.35;
uniform float play_half = 22.0;
uniform vec4 paving : source_color = vec4(0.80, 0.77, 0.70, 1.0);
uniform vec4 dirt : source_color = vec4(0.86, 0.72, 0.52, 1.0);
uniform vec4 cobble : source_color = vec4(0.82, 0.80, 0.76, 1.0);
uniform vec4 sand : source_color = vec4(0.94, 0.88, 0.68, 1.0);
uniform vec4 under : source_color = vec4(0.40, 0.48, 0.30, 1.0);

varying vec3 v_world;
varying vec3 v_wnormal;

void vertex() {
	v_world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	v_wnormal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

// detail albedo + tangent normal of one material slice on the ground plane
vec4 ground_mat(vec2 xz, float layer, float scale, float bump, inout vec3 tn, float w) {
	vec2 uv = xz * scale;
	tn += mat_tangent_normal(uv, layer, bump) * w;
	return texture(mat_albedo, vec3(uv, layer));
}

void fragment() {
	vec2 xz = v_world.xz;
	vec2 muv = (xz - vec2(terrain_origin)) / terrain_size;
	vec4 m = texture(mask_tex, muv);
	float n = fbm(xz * 0.35);
	float fine = noise(xz * 4.0);
	float edge_n = (noise(xz * 2.5) - 0.5) * 0.35;
	// --- material weights
	float trod = smoothstep(0.1, 0.9, m.b) * (0.6 + fine * 0.4) * 0.45;
	float dp = smoothstep(0.35, 0.6, m.r + edge_n);
	float cp = smoothstep(0.35, 0.6, m.g + edge_n);
	float pp = smoothstep(0.35, 0.6, m.a + edge_n * 0.4);
	float bank = (1.0 - smoothstep(water_level + 0.05, water_level + 0.45 + n * 0.2, v_world.y)) * 0.85;
	float wet = (1.0 - smoothstep(water_level - 0.2, water_level + 0.02, v_world.y)) * 0.7;
	float steep = (1.0 - smoothstep(0.55, 0.8, v_wnormal.y)) * 0.7;
	// --- textured layers (all fetched unconditionally: no divergent derivatives)
	vec3 tg = vec3(0.0);
	vec3 td = vec3(0.0);
	vec3 tc = vec3(0.0);
	vec3 tp = vec3(0.0);
	vec3 ts = vec3(0.0);
	// meadow detail at two scales (one rotated) so the tiling never shows
	vec2 xz_r = mat2(vec2(0.8, 0.6), vec2(-0.6, 0.8)) * xz;
	vec4 a_g = ground_mat(xz, 12.0, 0.31, 0.45, tg, 0.5) * 0.5 + ground_mat(xz_r + 17.0, 12.0, 0.13, 0.45, tg, 0.5) * 0.5;
	vec4 a_d = ground_mat(xz, 13.0, 0.5, 0.9, td, 1.0);
	vec4 a_c = ground_mat(xz, 10.0, 0.62, 1.0, tc, 1.0);
	vec4 a_p = ground_mat(xz, 14.0, 0.42, 1.0, tp, 1.0);
	vec4 a_s = ground_mat(xz, 15.0, 0.5, 0.7, ts, 1.0);
	// --- colours
	vec3 g = meadow_base(xz, v_world.y) * a_g.rgb * 2.0;
	// beneath the grass carpet the ground takes the blades' root shade;
	// beyond the grass draw distance it shows their average colour instead
	float grassy = (1.0 - smoothstep(0.2, 0.4, max(m.r, max(m.g, m.a)))) * (1.0 - smoothstep(0.5, 0.75, m.b));
	grassy *= 1.0 - smoothstep(play_half + 2.0, play_half + 4.0, max(abs(xz.x), abs(xz.y)));
	float far = smoothstep(GRASS_FADE_START, GRASS_FADE_END, length(CAMERA_POSITION_WORLD - v_world));
	g *= mix(1.0, mix(GRASS_ROOT_SHADE, 1.0, far), grassy);
	vec3 dcol = dirt.rgb * a_d.rgb * 2.0;
	vec3 col = mix(g, mix(g, dcol, 0.6), trod);
	vec3 tn = mix(tg, td, trod);
	float rough = mix(a_g.a, a_d.a, trod);
	col = mix(col, dcol, dp);
	tn = mix(tn, td, dp);
	col = mix(col, cobble.rgb * a_c.rgb * 2.0, cp);
	tn = mix(tn, tc, cp);
	rough = mix(rough, a_c.a, cp);
	col = mix(col, paving.rgb * a_p.rgb * 2.0, pp);
	tn = mix(tn, tp, pp);
	rough = mix(rough, a_p.a, pp);
	col = mix(col, sand.rgb * a_s.rgb * 2.0, bank);
	tn = mix(tn, ts, bank);
	col = mix(col, under.rgb * 0.8, wet);
	col = mix(col, dcol * 0.85, steep);
	tn = mix(tn, td, steep);
	// soft vignette into the surrounding wilds
	float edge = max(abs(xz.x), abs(xz.y));
	col *= mix(1.0, 0.82, smoothstep(play_half, play_half + 8.0, edge));
	// snow blanket
	float snow = snow_amount * smoothstep(0.4, 0.75, v_wnormal.y) * (1.0 - wet);
	snow *= mix(1.0, 0.75, dp * 0.6 + cp * 0.6 + pp * 0.6);
	col = mix(col, vec3(0.93, 0.95, 1.0) * (0.95 + fine * 0.05), snow);
	tn = normalize(mix(tn, vec3(0.0, 0.0, 1.0), snow * 0.7));
	// ground plane frame: u = world +X, v = world +Z
	vec3 wn = normalize(v_wnormal);
	vec3 wt = normalize(vec3(1.0, 0.0, 0.0) - wn * wn.x);
	vec3 wb = normalize(cross(wt, wn));
	vec3 world_n = normalize(wt * tn.x + wb * tn.y + wn * tn.z);
	NORMAL = normalize((VIEW_MATRIX * vec4(world_n, 0.0)).xyz);
	ALBEDO = col;
	ROUGHNESS = rough;
}
