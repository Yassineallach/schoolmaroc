// Full-screen camera blur for the distance (the tilt-shift miniature look):
// everything past far_start softens more and more until far_end, so the
// woods running to the horizon melt into a soft painted backdrop. Reads the
// depth buffer directly, so it works with MSAA and on every renderer
// (Godot's own depth of field blurs the whole screen with MSAA on Mobile).
// The glade itself (and its water, which the screen copy doesn't hold) is
// never blurred, only the land beyond it; the sky is left alone too, so
// clouds stay crisp.
shader_type spatial;
render_mode unshaded, depth_draw_never, depth_test_disabled, cull_disabled, fog_disabled, shadows_disabled;

uniform sampler2D screen_tex : hint_screen_texture, filter_linear_mipmap, repeat_disable;
uniform sampler2D depth_tex : hint_depth_texture, filter_nearest, repeat_disable;
uniform float far_start = 50.0;
uniform float far_end = 120.0;
uniform float max_radius = 10.0; // pixels at full blur
uniform float glade_half = 26.0; // blur starts outside this square (world metres)

void vertex() {
	POSITION = vec4(VERTEX.xy * 2.0, 1.0, 1.0);
}

vec3 view_pos(vec2 uv, mat4 inv_proj) {
	float d = texture(depth_tex, uv).r;
#if CURRENT_RENDERER == RENDERER_COMPATIBILITY
	vec3 ndc = vec3(uv, d) * 2.0 - 1.0;
#else
	vec3 ndc = vec3(uv * 2.0 - 1.0, d);
#endif
	vec4 v = inv_proj * vec4(ndc, 1.0);
	return v.xyz / v.w;
}

float linear_depth(vec2 uv, mat4 inv_proj) {
	return -view_pos(uv, inv_proj).z;
}

void fragment() {
	vec2 uv = SCREEN_UV;
#if CURRENT_RENDERER == RENDERER_COMPATIBILITY
	bool sky = texture(depth_tex, uv).r >= 0.99999;
#else
	bool sky = texture(depth_tex, uv).r <= 0.00001;
#endif
	vec3 vp = view_pos(uv, INV_PROJECTION_MATRIX);
	vec3 world = (INV_VIEW_MATRIX * vec4(vp, 1.0)).xyz;
	float out_d = max(abs(world.x), abs(world.z));
	float k = smoothstep(far_start, far_end, -vp.z) * smoothstep(glade_half, glade_half + 14.0, out_d);
	if (sky || k < 0.02) {
		discard;
	}
	vec2 px = 1.0 / VIEWPORT_SIZE;
	float r = max_radius * k;
	float lod = log2(max(r * 0.5, 1.0));
	// a ring of taps from a mip level that already averages the gaps between them
	vec3 sum = textureLod(screen_tex, uv, lod).rgb * 2.0;
	float w = 2.0;
	for (int i = 0; i < 8; i++) {
		float a = float(i) * 0.785398 + 0.3;
		vec2 o = vec2(cos(a), sin(a)) * r * px;
		vec2 suv = clamp(uv + o, vec2(0.0), vec2(1.0));
		// don't bleed sharp, near things into the blurred distance
		float zt = linear_depth(suv, INV_PROJECTION_MATRIX);
		float wt = smoothstep(far_start * 0.8, far_start, zt);
		sum += textureLod(screen_tex, suv, lod).rgb * wt;
		w += wt;
	}
	ALBEDO = sum / w;
	ALPHA = smoothstep(0.02, 0.25, k);
}
