// Full-screen contact shading (Mobile + Compatibility: only depth needed).
// Measures how concave the depth buffer is around each pixel using pairs of
// opposite samples at two radii: flat or sloped surfaces cancel out, while
// creases (stone joints, wall bases, under roof eaves, around window frames,
// grass against the ground) darken softly. Multiplied over the image.
shader_type spatial;
render_mode unshaded, depth_draw_never, depth_test_disabled, cull_disabled, blend_mul, fog_disabled, shadows_disabled;

uniform sampler2D depth_tex : hint_depth_texture, filter_nearest, repeat_disable;
uniform float strength = 0.75;
uniform float radius_small = 0.12; // metres: joints and contact
uniform float radius_large = 0.55; // metres: corners, eaves, wall bases
uniform float fade_start = 45.0;
uniform float fade_end = 110.0;
uniform vec3 shade_tint = vec3(0.86, 0.9, 1.0); // occlusion is cool, never black

void vertex() {
	POSITION = vec4(VERTEX.xy * 2.0, 1.0, 1.0);
}

float linear_depth(vec2 uv, mat4 inv_proj) {
	float d = texture(depth_tex, uv).r;
#if CURRENT_RENDERER == RENDERER_COMPATIBILITY
	vec3 ndc = vec3(uv, d) * 2.0 - 1.0;
#else
	vec3 ndc = vec3(uv * 2.0 - 1.0, d);
#endif
	vec4 v = inv_proj * vec4(ndc, 1.0);
	return -v.z / v.w;
}

float pair_occ(vec2 uv, vec2 o, float d0, float range, mat4 ip) {
	float a = linear_depth(uv + o, ip);
	float b = linear_depth(uv - o, ip);
	// ignore pairs that straddle a silhouette (no halos)
	float valid = step(abs(a - d0), range) * step(abs(b - d0), range);
	float concave = d0 - (a + b) * 0.5;
	return clamp(concave / (range * 0.35), 0.0, 1.0) * valid;
}

void fragment() {
	float d0 = linear_depth(SCREEN_UV, INV_PROJECTION_MATRIX);
	float fade = 1.0 - smoothstep(fade_start, fade_end, d0);
	float occ = 0.0;
	if (fade > 0.0 && d0 < 500.0) {
		// convert world radii to screen offsets at this depth
		float px_per_m = PROJECTION_MATRIX[1][1] * 0.5 / d0;
		vec2 aspect = vec2(VIEWPORT_SIZE.y / VIEWPORT_SIZE.x, 1.0);
		float rs = radius_small * px_per_m;
		float rl = radius_large * px_per_m;
		// rotate the sample pattern per pixel to trade banding for fine noise
		float ang = fract(sin(dot(FRAGCOORD.xy, vec2(12.9898, 78.233))) * 43758.5453) * 3.14159;
		for (int i = 0; i < 4; i++) {
			float a = ang + float(i) * 0.785398;
			vec2 dir = vec2(cos(a), sin(a)) * aspect;
			occ += pair_occ(SCREEN_UV, dir * rs, d0, radius_small * 3.0, INV_PROJECTION_MATRIX) * 0.55;
			occ += pair_occ(SCREEN_UV, dir * rl, d0, radius_large * 2.0, INV_PROJECTION_MATRIX) * 0.45;
		}
		occ = clamp(occ / 4.0, 0.0, 1.0) * fade;
	}
	float k = occ * strength;
	ALBEDO = mix(vec3(1.0), shade_tint * 0.55, k);
}
