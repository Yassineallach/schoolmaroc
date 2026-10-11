// Procedural architecture material for walls, cottages, towers and roofs.
// Vertex colour RGB = tint, vertex colour ALPHA = surface zone:
//   0.00 plaster   0.25 stone masonry   0.50 timber/planks
//   0.75 roof tiles   1.00 plain (trim, ridge, quoins)
// UV is in metres: x along the surface, y up the surface.
shader_type spatial;
render_mode diffuse_lambert_wrap, specular_schlick_ggx;

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

// Irregular running-bond stones. Returns (mortar mask, per-stone random).
vec2 stones(vec2 uv) {
	float row_h = 0.32;
	float row = floor(uv.y / row_h);
	float rnd_row = hash12(vec2(row, 7.0));
	float h = row_h;
	float w = 0.48 + rnd_row * 0.22;
	vec2 p = vec2(uv.x + row * 0.37 + rnd_row, uv.y);
	float col = floor(p.x / w);
	float id = hash12(vec2(col, row));
	vec2 f = vec2(fract(p.x / w) * w, fract(uv.y / row_h) * h);
	// wobble the joints so stones look hand-cut
	float wob = (noise(uv * 6.0) - 0.5) * 0.05;
	float edge = min(min(f.x, w - f.x), min(f.y, h - f.y)) + wob;
	float mortar = 1.0 - smoothstep(0.012, 0.04, edge);
	return vec2(mortar, id);
}

vec2 tiles(vec2 uv) {
	float row_h = 0.22;
	float row = floor(uv.y / row_h);
	float w = 0.26;
	float x = uv.x + mod(row, 2.0) * w * 0.5;
	float col = floor(x / w);
	float fx = fract(x / w) - 0.5;
	float fy = fract(uv.y / row_h);
	// rounded "fish scale" bottom edge of each tile
	float scallop = fy - (1.0 - sqrt(max(0.0, 0.25 - fx * fx)) * 0.9);
	float shade = smoothstep(-0.1, 0.25, fy) * 0.25 + 0.75;
	float gap = 1.0 - smoothstep(0.42, 0.5, abs(fx));
	return vec2(shade * mix(0.82, 1.0, gap) * (scallop < 0.0 ? 0.9 : 1.0), hash12(vec2(col, row)));
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
	vec3 col;
	float rough = 0.92;
	float n = fbm(uv * 3.0);
	if (zone < 0.125) {
		// plaster: soft blotches, darker dirt near the ground
		col = tint * (0.93 + n * 0.1);
		float dirt = 1.0 - smoothstep(0.0, 0.9, v_world.y - base_height);
		col *= 1.0 - dirt * 0.18;
	} else if (zone < 0.375) {
		vec2 st = stones(uv);
		vec3 stone = tint * (0.82 + st.y * 0.3) * (0.92 + n * 0.16);
		col = mix(stone, tint * 0.55, st.x);
	} else if (zone < 0.625) {
		float grain = noise(vec2(uv.x * 30.0, uv.y * 2.0));
		float plank = smoothstep(0.0, 0.03, abs(fract(uv.x * 4.0) - 0.5) - 0.46);
		col = tint * (0.85 + grain * 0.25) * mix(1.0, 0.75, plank);
	} else if (zone < 0.875) {
		vec2 tl = tiles(uv);
		col = tint * tl.x * (0.88 + tl.y * 0.22);
		rough = 0.75;
	} else {
		col = tint * (0.95 + n * 0.08);
	}
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
	SPECULAR = 0.25;
}
