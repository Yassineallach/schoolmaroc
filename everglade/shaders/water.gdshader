// Pond water: depth-tinted from the terrain height texture, foamy shores,
// gentle ripples and sun glints. No screen textures needed (mobile friendly).
shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_disabled, specular_schlick_ggx;

global uniform float night;
global uniform float snow_amount;

uniform sampler2D height_tex : filter_linear, repeat_disable;
uniform float terrain_origin = -32.0;
uniform float terrain_size = 64.0;
uniform float water_level = -0.35;
uniform vec4 shallow : source_color = vec4(0.42, 0.86, 0.90, 1.0);
uniform vec4 deep : source_color = vec4(0.12, 0.46, 0.78, 1.0);

varying vec3 v_world;

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

void vertex() {
	v_world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	VERTEX.y += sin(v_world.x * 1.3 + TIME * 1.2) * 0.012 + cos(v_world.z * 1.1 + TIME) * 0.012;
}

void fragment() {
	vec2 xz = v_world.xz;
	vec2 huv = ((xz - vec2(terrain_origin)) / terrain_size * 128.0 + 0.5) / 129.0;
	float ground = texture(height_tex, huv).r;
	float depth = water_level - ground;
	if (depth < -0.02) {
		discard;
	}
	vec2 flow = vec2(TIME * 0.05, TIME * 0.03);
	float r1 = noise(xz * 1.6 + flow);
	float r2 = noise(xz * 3.1 - flow * 1.7);
	float ripple = r1 * 0.6 + r2 * 0.4;
	// anime water: banded depth colours, crisp foam lines and sparkles
	float band = floor(smoothstep(0.0, 1.0, depth) * 3.0) / 3.0;
	vec3 col = mix(shallow.rgb, deep.rgb, band);
	float foam_line = step(depth, 0.06 + ripple * 0.05);
	float foam_ring = step(abs(depth - (0.16 + 0.04 * sin(TIME * 0.8 + ripple * 4.0))), 0.012);
	float foam = clamp(foam_line + foam_ring * 0.8, 0.0, 1.0);
	col = mix(col, vec3(1.0), foam * 0.9);
	float glint = step(0.93, noise(xz * 6.0 + vec2(TIME * 0.3, -TIME * 0.2))) * step(0.6, r1);
	col = mix(col, vec3(1.0), glint * (1.0 - night) * 0.9);
	// frozen in deep winter
	col = mix(col, vec3(0.80, 0.88, 0.94), snow_amount * 0.65);
	ALBEDO = col;
	ALPHA = clamp(smoothstep(-0.02, 0.25, depth) * 0.85 + foam * 0.3, 0.0, 0.95);
	vec3 bump = normalize(vec3((r1 - 0.5) * 0.35, 1.0, (r2 - 0.5) * 0.35));
	NORMAL = normalize((VIEW_MATRIX * vec4(bump, 0.0)).xyz);
	ROUGHNESS = mix(0.15, 0.5, snow_amount);
	SPECULAR = 0.3;
	EMISSION = col * night * 0.05;
}
