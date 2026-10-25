shader_type canvas_item;

// Edition shimmer, dissolve and pointer tilt for cards and charms.
// edition: 0 none, 1 foil, 2 holo, 3 chroma.
// tilt: where the pointer sits on the face, -1..1 per axis; tilt_amt eases
// it in and out. The side under the pointer sinks away (it draws smaller,
// as if further off), the opposite side rises and catches a little light.
uniform int edition = 0;
uniform vec2 size = vec2(100.0, 140.0);
uniform float dissolve : hint_range(0.0, 1.0) = 0.0;
uniform vec4 burn : source_color = vec4(1.0, 0.75, 0.3, 1.0);
uniform float phase = 0.0;
uniform vec2 tilt = vec2(0.0);
uniform float tilt_amt = 0.0;
// Balatro's debuff.fs: a dull red veil and a red X over a debuffed card
uniform bool debuff = false;

const float TILT_DEPTH = 0.22;

varying vec2 local;

void vertex() {
	local = VERTEX;
	if (tilt_amt > 0.0) {
		vec2 half_size = size * 0.5;
		vec2 p = VERTEX - half_size;
		float depth = dot(p / half_size, tilt) * tilt_amt * TILT_DEPTH;
		VERTEX = half_size + p / (1.0 + max(depth, -0.5));
	}
}

vec3 hue(float h) {
	return clamp(abs(fract(h + vec3(0.0, 2.0 / 3.0, 1.0 / 3.0)) * 6.0 - 3.0) - 1.0, 0.0, 1.0);
}

// debuff.fs's HSL round trip
float hue_part(float s, float t, float h) {
	float hs = mod(h, 1.0) * 6.0;
	if (hs < 1.0) return (t - s) * hs + s;
	if (hs < 3.0) return t;
	if (hs < 4.0) return (t - s) * (4.0 - hs) + s;
	return s;
}

vec3 hsl_to_rgb(vec3 c) {
	if (c.y == 0.0) return vec3(c.z);
	float t = (c.z < 0.5) ? c.y * c.z + c.z : -c.y * c.z + (c.y + c.z);
	float s = 2.0 * c.z - t;
	return vec3(hue_part(s, t, c.x + 1.0 / 3.0), hue_part(s, t, c.x), hue_part(s, t, c.x - 1.0 / 3.0));
}

vec3 rgb_to_hsl(vec3 c) {
	float low = min(c.r, min(c.g, c.b));
	float high = max(c.r, max(c.g, c.b));
	float delta = high - low;
	float sum = high + low;
	vec3 hsl = vec3(0.0, 0.0, 0.5 * sum);
	if (delta == 0.0) return hsl;
	hsl.y = (hsl.z < 0.5) ? delta / sum : delta / (2.0 - sum);
	if (high == c.r) hsl.x = (c.g - c.b) / delta;
	else if (high == c.g) hsl.x = (c.b - c.r) / delta + 2.0;
	else hsl.x = (c.r - c.g) / delta + 4.0;
	hsl.x = mod(hsl.x / 6.0, 1.0);
	return hsl;
}

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void fragment() {
	vec4 c = COLOR;
	vec2 uv = local / size;
	float t = TIME * 0.6 + phase;
	// Only the opaque face shimmers; soft shadows stay plain.
	float face = step(0.9, c.a);
	if (edition == 1) {
		float band = sin((uv.x + uv.y) * 9.0 - t * 3.0);
		float s = smoothstep(0.55, 1.0, band);
		c.rgb = mix(c.rgb, c.rgb * 0.85 + vec3(0.55, 0.75, 1.0) * 0.45, face * (0.25 + 0.35 * s));
	} else if (edition == 2) {
		float h = 0.55 + 0.12 * sin(uv.y * 6.0 + t * 2.0) + 0.1 * uv.x;
		float s = 0.5 + 0.5 * sin((uv.x - uv.y) * 14.0 + t * 2.5);
		c.rgb = mix(c.rgb, c.rgb * hue(h) * 1.25 + hue(h + 0.5) * 0.12, face * (0.35 + 0.2 * s));
	} else if (edition == 3) {
		float h = fract(uv.x * 0.6 + uv.y * 0.4 + t * 0.25);
		c.rgb = mix(c.rgb, c.rgb * (0.6 + 0.7 * hue(h)), face * 0.6);
	} else if (edition == 4) {
		// negative: inverted colours with a slow violet sheen
		vec3 inv = vec3(1.0) - c.rgb;
		float s = 0.5 + 0.5 * sin((uv.x + uv.y) * 6.0 - t * 1.5);
		c.rgb = mix(c.rgb, inv * vec3(0.85, 0.8, 1.0) + vec3(0.08, 0.0, 0.15) * s, face);
	}
	if (debuff) {
		// debuff.fs, drawn over the card: everything dimmed and pulled
		// toward red at 30%, and a solid red X corner to corner
		vec3 sat = rgb_to_hsl(c.rgb * 0.8 + 0.2 * vec3(1.0, 0.0, 0.0));
		sat.y = 0.5;
		float width = 0.1;
		bool on_x = (uv.x + uv.y > 1.0 - width && uv.x + uv.y < 1.0 + width)
				|| ((1.0 - uv.x) + uv.y > 1.0 - width && (1.0 - uv.x) + uv.y < 1.0 + width);
		if (on_x) {
			sat = vec3(1.0, 0.7, 0.8 * sat.z);
		} else {
			sat.y *= 0.5;
			sat.z *= 0.7;
		}
		c.rgb = mix(c.rgb, hsl_to_rgb(sat), (on_x ? 1.0 : 0.3) * face);
	}
	if (tilt_amt > 0.0) {
		// raised side brighter, sunken side a touch darker
		float lit = dot(uv - 0.5, -tilt) * tilt_amt;
		c.rgb = clamp(c.rgb + face * vec3(lit * 0.22), 0.0, 1.0);
	}
	if (dissolve > 0.0) {
		// Blocky noise so the dissolve reads as pixels burning away.
		float n = hash(floor(local / 5.0));
		float edge = dissolve * 1.15 - 0.075;
		if (n < edge) {
			discard;
		}
		c.rgb = mix(c.rgb, burn.rgb, step(n, edge + 0.08) * face);
	}
	COLOR = c;
}
