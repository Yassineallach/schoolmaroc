// Painted leaf-card foliage (stylised fantasy look): leaf-cluster texture
// tinted by the vertex colour gradient, alpha-scissored, double-sided, lit
// with the canopy's spherical normals in three soft cel bands.
shader_type spatial;
render_mode cull_disabled, depth_prepass_alpha;

global uniform float wind_strength;
global uniform vec4 season_leaf : source_color;
global uniform float snow_amount;

uniform sampler2D leaf_tex : source_color, filter_linear_mipmap, repeat_disable;
uniform float alpha_cut = 0.45;

varying float v_channel;
varying vec3 v_world_normal;
varying vec3 v_world;

float hash12(vec2 p) {
	vec3 p3 = fract(vec3(p.xyx) * 0.1031);
	p3 += dot(p3, p3.yzx + 33.33);
	return fract((p3.x + p3.y) * p3.z);
}

void vertex() {
	v_channel = COLOR.a;
	vec3 origin = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	float phase = hash12(origin.xz) * 6.2831;
	float t = TIME * 1.2;
	float h = max(VERTEX.y, 0.0);
	// whole-crown sway plus a fluttery per-card ripple
	vec2 sway = vec2(sin(t + phase + VERTEX.y * 0.5), cos(t * 0.8 + phase)) * 0.03 * h;
	sway += vec2(sin(t * 3.3 + VERTEX.x * 3.0 + VERTEX.z * 2.0), cos(t * 2.9 + VERTEX.z * 3.0)) * 0.035;
	VERTEX.xz += sway * wind_strength;
	v_world_normal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	v_world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec4 tex = texture(leaf_tex, UV);
	if (tex.a < alpha_cut) {
		discard;
	}
	// dissolve near the camera
	float cam_d = length(VERTEX);
	if (cam_d < 4.0) {
		float hd = fract(sin(dot(floor(FRAGCOORD.xy), vec2(12.9898, 78.233))) * 43758.5453);
		if (smoothstep(1.2, 4.0, cam_d) < hd) {
			discard;
		}
	}
	// keep the canopy's spherical normal on both sides of each card
	if (!FRONT_FACING) {
		NORMAL = -NORMAL;
	}
	// natural, slightly muted greens (no fluorescent canopies)
	vec3 base_c = mix(vec3(dot(COLOR.rgb, vec3(0.3, 0.59, 0.11))), COLOR.rgb, 0.78) * 0.92;
	vec3 col = base_c * mix(0.5, 1.12, tex.r);
	// painted occlusion: crowns bright, undersides deep and cool
	float ny = v_world_normal.y;
	col *= mix(vec3(0.26, 0.34, 0.48), vec3(1.08, 1.06, 0.95), smoothstep(-0.35, 0.85, ny));
	// warm sunlit rim on the crown, cool lower shell
	col += vec3(0.08, 0.06, 0.0) * smoothstep(0.6, 0.95, ny) * tex.r;
	float foliage = 1.0 - smoothstep(0.08, 0.18, v_channel);
	float lum = dot(col, vec3(0.3, 0.59, 0.11));
	col = mix(col, season_leaf.rgb * lum * 2.4, foliage * season_leaf.a);
	float up = smoothstep(0.45, 0.85, v_world_normal.y);
	col = mix(col, vec3(0.94, 0.96, 1.0), up * snow_amount * 0.9);
	ALBEDO = col;
	ROUGHNESS = 1.0;
	SPECULAR = 0.0;
	BACKLIGHT = col * 0.25;
}

void light() {
	float ndl = dot(NORMAL, LIGHT);
	float wrap = (ndl + 0.2) / 1.2;
	float band = smoothstep(0.08, 0.16, wrap) * 0.45 + smoothstep(0.45, 0.52, wrap) * 0.3 + smoothstep(0.78, 0.84, wrap) * 0.25;
	float shadow = mix(0.22, 1.0, smoothstep(0.2, 0.6, ATTENUATION));
	DIFFUSE_LIGHT += LIGHT_COLOR / PI * band * shadow;
}
