// The land beyond the glade: the same painted meadow colours as the terrain
// (so the seam vanishes), rolling into hazy hills, with soft darker patches
// under the forest belt. Lit like the terrain; depth fog does the rest.
shader_type spatial;
render_mode diffuse_lambert_wrap;

#include "res://shaders/toon.gdshaderinc"
#include "res://shaders/materials.gdshaderinc"
#include "res://shaders/meadow.gdshaderinc"

uniform float play_half = 22.0;

varying vec3 v_world;
varying vec3 v_wn;

void vertex() {
	v_world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	v_wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec2 xz = v_world.xz;
	vec3 tn = vec3(0.0);
	vec2 xz_r = mat2(vec2(0.8, 0.6), vec2(-0.6, 0.8)) * xz;
	vec4 a = texture(mat_albedo, vec3(xz * 0.31, 12.0)) * 0.5 + texture(mat_albedo, vec3(xz_r * 0.13 + 17.0, 12.0)) * 0.5;
	vec3 col = meadow_base(xz, v_world.y) * a.rgb * 2.0;
	// woodland floor: darker, cooler ground where the forest belt grows
	float d = max(abs(xz.x), abs(xz.y));
	float wood = smoothstep(play_half + 1.0, play_half + 5.0, d) * (1.0 - smoothstep(70.0, 110.0, length(xz)));
	wood *= 0.55 + noise(xz * 0.07) * 0.45;
	col = mix(col, col * vec3(0.62, 0.7, 0.62), wood);
	ALBEDO = col;
	ROUGHNESS = 0.95;
	EMISSION = bounce_light(col, v_wn, 0.0) * 0.5;
}
