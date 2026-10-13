// Procedural architecture material for walls, cottages, towers and roofs.
// Vertex colour RGB = tint, vertex colour ALPHA = surface zone:
//   0.00 plaster   0.25 stone masonry   0.50 timber/planks
//   0.75 roof tiles   1.00 plain (trim, ridge, quoins)
// UV is in metres: x along the surface, y up the surface.
shader_type spatial;
render_mode diffuse_lambert_wrap;

#include "res://shaders/toon.gdshaderinc"
#include "res://shaders/materials.gdshaderinc"

global uniform float snow_amount;
global uniform vec4 season_ground : source_color;

uniform float build_progress = 1.0; // rise-from-ground animation
uniform float base_height = 0.0;
uniform float top_height = 10.0;
uniform float moss_amount = 0.6;

varying vec3 v_world;
varying vec3 v_wnormal;

float hash12(vec2 p) {
	vec3 p3 = fract(vec3(p.xyx) * 0.1031);
	p3 += dot(p3, p3.yzx + 33.33);
	return fract((p3.x + p3.y) * p3.z);
}

float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash12(i), hash12(i + vec2(1.0, 0.0)), u.x),
			mix(hash12(i + vec2(0.0, 1.0)), hash12(i + vec2(1.0, 1.0)), u.x), u.y);
}

float fbm(vec2 p) {
	float v = 0.0;
	float a = 0.5;
	for (int i = 0; i < 3; i++) {
		v += a * noise(p);
		p *= 2.03;
		a *= 0.5;
	}
	return v;
}

void vertex() {
	v_world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	v_wnormal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	if (v_world.y > mix(base_height - 1.0, top_height + 1.0, build_progress)) {
		discard;
	}
	float zone = COLOR.a;
	vec3 tint = COLOR.rgb;
	vec2 uv = UV;
	float n = fbm(uv * 3.0);
	// pick the material slice arithmetically so texture fetches (and their
	// derivatives) stay outside divergent branches
	float is_plaster = 1.0 - step(0.125, zone);
	float is_stone = step(0.125, zone) * (1.0 - step(0.375, zone));
	float is_wood = step(0.375, zone) * (1.0 - step(0.625, zone));
	float is_tiles = step(0.625, zone) * (1.0 - step(0.875, zone));
	float is_plain = step(0.875, zone);
	// plain = individually modelled stones and trims: fine weathered grain
	float layer = is_plaster * 5.0 + is_stone * 1.0 + is_wood * 3.0 + is_tiles * 6.0 + is_plain * 5.0;
	float sc = is_plaster * 0.55 + is_stone * 0.52 + is_wood * 1.0 + is_tiles * 0.57 + is_plain * 1.3;
	float flip = mix(1.0, -1.0, is_tiles); // tile lips face down the slope
	vec2 tuv = vec2(uv.x, uv.y * flip) * sc;
	// cotangent frame from screen derivatives (meshes carry no tangents)
	vec3 dp1 = dFdx(VERTEX);
	vec3 dp2 = dFdy(VERTEX);
	vec2 du1 = dFdx(UV);
	vec2 du2 = dFdy(UV);
	vec3 nn = normalize(NORMAL);
	vec3 dp2perp = cross(dp2, nn);
	vec3 dp1perp = cross(nn, dp1);
	vec3 T = dp2perp * du1.x + dp1perp * du2.x;
	vec3 B = dp2perp * du1.y + dp1perp * du2.y;
	float invmax = inversesqrt(max(max(dot(T, T), dot(B, B)), 1e-12));
	vec4 alb = texture(mat_albedo, vec3(tuv, layer));
	// lime render stays smooth and soft; stone and tiles keep their relief
	vec3 tn = mat_tangent_normal(tuv, layer, mix(0.6, 1.0, is_stone + is_tiles) * mix(1.0, 0.55, is_plain) * mix(1.0, 0.45, is_plaster));
	tn.y *= flip;
	NORMAL = normalize(mat3(T * invmax, B * invmax, nn) * tn);
	vec3 col = tint * mix(vec3(1.0), alb.rgb * 2.0, mix(1.0, 0.55, is_plaster));
	float rough = alb.a;
	// plaster gathers grime near the ground
	float dirt = 1.0 - smoothstep(0.0, 0.9, v_world.y - base_height);
	col *= 1.0 - dirt * 0.18 * is_plaster;
	// moss creeping on stone near the ground and on top ledges
	if (zone > 0.125 && zone < 0.375) {
		float ground_moss = 1.0 - smoothstep(0.0, 0.7 + n * 0.6, v_world.y - base_height);
		float top_moss = smoothstep(0.5, 0.9, v_wnormal.y) * 0.8;
		float m = clamp(max(ground_moss, top_moss) * moss_amount * smoothstep(0.35, 0.6, fbm(uv * 1.7)), 0.0, 1.0);
		col = mix(col, vec3(0.34, 0.46, 0.20) * season_ground.rgb, m * 0.75);
	}
	if (zone > 0.625 && zone < 0.875) {
		float rm = smoothstep(0.62, 0.8, fbm(uv * 0.9 + 3.0)) * 0.4;
		col = mix(col, vec3(0.42, 0.5, 0.25), rm * moss_amount);
	}
	float up = smoothstep(0.3, 0.75, v_wnormal.y);
	col = mix(col, vec3(0.93, 0.95, 1.0), up * snow_amount);
	ALBEDO = col;
	ROUGHNESS = rough;
}
