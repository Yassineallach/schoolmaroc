// Stylised vertex-coloured material shared by every Blender-made prop.
// Vertex colour alpha selects a channel (see blender/build_assets.py):
//   1.0 solid, 0.0 foliage (sway + season tint), 0.25 evergreen (sway),
//   0.5 petals/cloth (sway only).
shader_type spatial;
render_mode diffuse_lambert_wrap, specular_disabled;

global uniform float wind_strength;
global uniform vec4 season_leaf : source_color;
global uniform float snow_amount;
global uniform float night;

uniform float sway_scale = 1.0;
uniform float pop = 1.0;   // grow-in animation for freshly placed props (0..1)

varying float v_channel;
varying vec3 v_world_normal;
varying float v_height;

float hash12(vec2 p) {
	vec3 p3 = fract(vec3(p.xyx) * 0.1031);
	p3 += dot(p3, p3.yzx + 33.33);
	return fract((p3.x + p3.y) * p3.z);
}

void vertex() {
	v_channel = COLOR.a;
	v_height = VERTEX.y;
	vec3 world_origin = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	float sway_mask = 1.0 - step(0.75, COLOR.a);   // foliage & petals
	float phase = hash12(world_origin.xz) * 6.2831;
	float h = max(VERTEX.y, 0.0);
	float t = TIME * (1.1 + phase * 0.05);
	vec2 sway = vec2(sin(t + phase + VERTEX.y * 0.6), cos(t * 0.8 + phase)) * 0.025 * h;
	sway += vec2(sin(t * 3.1 + VERTEX.x * 4.0 + phase), sin(t * 2.7 + VERTEX.z * 4.0)) * 0.012;
	VERTEX.xz += sway * sway_mask * wind_strength * sway_scale;
	VERTEX *= pop;
	v_world_normal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec3 col = COLOR.rgb;
	// season tint only on deciduous foliage (alpha 0); evergreens (0.25) keep their colour
	float foliage = 1.0 - smoothstep(0.08, 0.18, v_channel);
	float lum = dot(col, vec3(0.3, 0.59, 0.11));
	col = mix(col, season_leaf.rgb * lum * 2.4, foliage * season_leaf.a);
	// soft ambient occlusion towards the ground
	col *= mix(0.72, 1.0, smoothstep(0.0, 0.8, v_height));
	// snow on upward-facing surfaces
	float up = smoothstep(0.35, 0.8, v_world_normal.y);
	col = mix(col, vec3(0.94, 0.96, 1.0), up * snow_amount);
	ALBEDO = col;
	ROUGHNESS = 0.9;
	BACKLIGHT = vec3(0.25, 0.3, 0.1) * foliage;
}
