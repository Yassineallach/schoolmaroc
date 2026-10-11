// Full-screen anime ink lines from depth discontinuities (works on the
// Mobile and Compatibility renderers - only the depth texture is needed).
shader_type spatial;
render_mode unshaded, depth_draw_never, depth_test_disabled, cull_disabled, blend_mix, fog_disabled, shadows_disabled;

uniform sampler2D depth_tex : hint_depth_texture, filter_nearest, repeat_disable;
uniform vec4 line_color : source_color = vec4(0.20, 0.14, 0.20, 0.85);
uniform float thickness = 1.2;
uniform float sensitivity = 0.035;
uniform float fade_start = 55.0;
uniform float fade_end = 140.0;

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

void fragment() {
	vec2 px = thickness / VIEWPORT_SIZE;
	float d0 = linear_depth(SCREEN_UV, INV_PROJECTION_MATRIX);
	float dl = linear_depth(SCREEN_UV + vec2(-px.x, 0.0), INV_PROJECTION_MATRIX);
	float dr = linear_depth(SCREEN_UV + vec2(px.x, 0.0), INV_PROJECTION_MATRIX);
	float du = linear_depth(SCREEN_UV + vec2(0.0, -px.y), INV_PROJECTION_MATRIX);
	float dd = linear_depth(SCREEN_UV + vec2(0.0, px.y), INV_PROJECTION_MATRIX);
	// only the nearer side of a discontinuity draws, so lines hug silhouettes
	float diff = max(max(d0 - dl, d0 - dr), max(d0 - du, d0 - dd));
	float edge = smoothstep(sensitivity, sensitivity * 2.2, diff / max(d0, 0.001));
	edge *= 1.0 - smoothstep(fade_start, fade_end, d0);
	ALBEDO = line_color.rgb;
	ALPHA = edge * line_color.a;
}
