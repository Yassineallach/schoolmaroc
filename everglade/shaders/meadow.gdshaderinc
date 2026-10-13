// Shared meadow colouring: the terrain and the grass blades both call
// meadow_base() so every blade's roots melt seamlessly into the painted
// ground beneath it (lush greens, sunlit lime patches, golden drifts).
global uniform vec4 season_ground : source_color;

const vec3 GRASS_A = vec3(0.32, 0.50, 0.23);
const vec3 GRASS_B = vec3(0.48, 0.61, 0.29);
const vec3 GRASS_GOLD = vec3(0.64, 0.62, 0.35);
// the ground under the grass carpet is shaded like the blade roots, which
// gives the meadow depth (dark between blades, bright tips)
const float GRASS_ROOT_SHADE = 0.8;
const float GRASS_FADE_START = 24.0;
const float GRASS_FADE_END = 34.0;

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

// golden drift amount (matches GrassField's GDScript twin)
float meadow_gold(vec2 xz) {
	return smoothstep(0.58, 0.7, fbm(xz * 0.09 + 11.0));
}

vec3 meadow_base(vec2 xz, float y) {
	float n = fbm(xz * 0.35);
	vec3 g = mix(GRASS_A, GRASS_B, smoothstep(0.42, 0.5, n) * 0.6 + smoothstep(0.6, 0.66, n) * 0.4);
	g = mix(g, GRASS_GOLD, meadow_gold(xz) * 0.6);
	g *= season_ground.rgb;
	// darker in hollows, sunnier on crests
	g *= mix(0.86, 1.04, smoothstep(-1.0, 1.5, y));
	return g;
}
