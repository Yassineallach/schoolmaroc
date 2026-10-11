// Meadow terrain: lush grass, painted paths (mask R = dirt, G = cobble,
// B = trodden ground around structures), sandy pond banks and seasonal snow.
shader_type spatial;
render_mode diffuse_lambert_wrap, specular_disabled;

global uniform vec4 season_ground : source_color;
global uniform float snow_amount;

uniform sampler2D mask_tex : filter_linear, repeat_disable;
uniform float terrain_origin = -32.0;
uniform float terrain_size = 64.0;
uniform float water_level = -0.35;
uniform float play_half = 22.0;
uniform vec4 grass_a : source_color = vec4(0.47, 0.66, 0.29, 1.0);
uniform vec4 grass_b : source_color = vec4(0.58, 0.72, 0.32, 1.0);
uniform vec4 dirt : source_color = vec4(0.66, 0.55, 0.40, 1.0);
uniform vec4 cobble : source_color = vec4(0.70, 0.67, 0.61, 1.0);
uniform vec4 sand : source_color = vec4(0.78, 0.72, 0.55, 1.0);
uniform vec4 under : source_color = vec4(0.40, 0.48, 0.30, 1.0);

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
	for (int i = 0; i < 4; i++) {
		v += a * noise(p);
		p *= 2.1;
		a *= 0.5;
	}
	return v;
}

// cellular cobbles: returns distance to the cell border (0 at mortar)
vec2 voronoi(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	float d1 = 8.0;
	float d2 = 8.0;
	float id = 0.0;
	for (int y = -1; y <= 1; y++) {
		for (int x = -1; x <= 1; x++) {
			vec2 g = vec2(float(x), float(y));
			vec2 o = vec2(hash12(i + g), hash12(i + g + 17.0)) * 0.8 + 0.1;
			float d = length(g + o - f);
			if (d < d1) {
				d2 = d1;
				d1 = d;
				id = hash12(i + g + 3.0);
			} else if (d < d2) {
				d2 = d;
			}
		}
	}
	return vec2(d2 - d1, id);
}

void vertex() {
	v_world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	v_wnormal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec2 xz = v_world.xz;
	vec2 muv = (xz - vec2(terrain_origin)) / terrain_size;
	vec4 m = texture(mask_tex, muv);
	float n = fbm(xz * 0.35);
	float fine = noise(xz * 4.0);
	vec3 g = mix(grass_a.rgb, grass_b.rgb, smoothstep(0.3, 0.75, n));
	g *= 0.92 + fine * 0.12;
	g *= season_ground.rgb;
	// darker in hollows, sunnier on crests
	g *= mix(0.86, 1.04, smoothstep(-1.0, 1.5, v_world.y));
	vec3 col = g;
	// trodden ground around buildings
	col = mix(col, mix(g, dirt.rgb, 0.45), smoothstep(0.1, 0.9, m.b) * (0.6 + fine * 0.4));
	// dirt paths with ragged edges
	float edge_n = (noise(xz * 2.5) - 0.5) * 0.35;
	float dp = smoothstep(0.35, 0.6, m.r + edge_n);
	vec3 dcol = dirt.rgb * (0.88 + fine * 0.18) * mix(1.0, 0.9, noise(xz * 9.0));
	col = mix(col, dcol, dp);
	// cobbles
	float cp = smoothstep(0.35, 0.6, m.g + edge_n);
	vec2 vor = voronoi(xz * 3.2);
	vec3 ccol = cobble.rgb * (0.82 + vor.y * 0.3);
	ccol = mix(dirt.rgb * 0.7, ccol, smoothstep(0.03, 0.12, vor.x));
	col = mix(col, ccol, cp);
	// sandy pond banks & wet underwater ground
	float bank = 1.0 - smoothstep(water_level + 0.05, water_level + 0.45 + n * 0.2, v_world.y);
	col = mix(col, sand.rgb * (0.9 + fine * 0.15), bank * 0.85);
	float wet = 1.0 - smoothstep(water_level - 0.2, water_level + 0.02, v_world.y);
	col = mix(col, under.rgb * 0.8, wet * 0.7);
	// steep slopes reveal earth
	float steep = 1.0 - smoothstep(0.55, 0.8, v_wnormal.y);
	col = mix(col, dirt.rgb * 0.8, steep * 0.7);
	// soft vignette into the surrounding wilds
	float edge = max(abs(xz.x), abs(xz.y));
	col *= mix(1.0, 0.82, smoothstep(play_half, play_half + 8.0, edge));
	// snow blanket
	float snow = snow_amount * smoothstep(0.4, 0.75, v_wnormal.y) * (1.0 - wet);
	snow *= mix(1.0, 0.75, dp * 0.6 + cp * 0.6);
	col = mix(col, vec3(0.93, 0.95, 1.0) * (0.95 + fine * 0.05), snow);
	ALBEDO = col;
	ROUGHNESS = 0.95;
}
