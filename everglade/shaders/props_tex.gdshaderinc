// Painted-texture variant of props.gdshader for the Quaternius kit models
// (doors, windows, fences, flowers, stones...): albedo comes from the model's
// own texture times its vertex colour, while sway, season tint, snow, ground
// occlusion, near-camera dissolve and bounce light match every other prop.
// Vertex colour alpha: 1 solid, 0 foliage (sway + season), 0.5 petals (sway).
// Include after `shader_type` / `render_mode`; define CUTOUT for alpha-cut cards.
#include "res://shaders/toon.gdshaderinc"
#include "res://shaders/materials.gdshaderinc"

global uniform float wind_strength;
global uniform vec4 season_leaf : source_color;
global uniform float snow_amount;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float alpha_cut = 0.4;
uniform float pop = 1.0;

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
	float sway_mask = 1.0 - step(0.75, COLOR.a);
	float phase = hash12(world_origin.xz) * 6.2831;
	float h = max(VERTEX.y, 0.0);
	float t = TIME * (1.1 + phase * 0.05);
	vec2 sway = vec2(sin(t + phase + VERTEX.y * 0.6), cos(t * 0.8 + phase)) * 0.05 * h;
	sway += vec2(sin(t * 3.1 + VERTEX.x * 4.0 + phase), sin(t * 2.7 + VERTEX.z * 4.0)) * 0.01;
	VERTEX.xz += sway * sway_mask * wind_strength;
	VERTEX *= pop;
	v_world_normal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec4 tex = texture(albedo_tex, UV);
#ifdef CUTOUT
	if (tex.a < alpha_cut) {
		discard;
	}
	if (!FRONT_FACING) {
		NORMAL = -NORMAL;
	}
#endif
	float cam_d = length(VERTEX);
	if (cam_d < 4.0) {
		float hd = fract(sin(dot(floor(FRAGCOORD.xy), vec2(12.9898, 78.233))) * 43758.5453);
		if (smoothstep(1.2, 4.0, cam_d) < hd) {
			discard;
		}
	}
	vec3 col = tex.rgb * COLOR.rgb;
	float foliage = 1.0 - smoothstep(0.08, 0.18, v_channel);
	float lum = dot(col, vec3(0.3, 0.59, 0.11));
	col = mix(col, season_leaf.rgb * lum * 2.4, foliage * season_leaf.a);
	col *= mix(0.72, 1.0, smoothstep(0.0, 0.8, v_height));
	float up = smoothstep(0.35, 0.8, v_world_normal.y);
	col = mix(col, vec3(0.94, 0.96, 1.0), up * snow_amount);
	ALBEDO = col;
	ROUGHNESS = 0.85;
	EMISSION = bounce_light(col, v_world_normal, v_height);
	BACKLIGHT = vec3(0.18, 0.22, 0.08) * (1.0 - step(0.75, v_channel));
}
