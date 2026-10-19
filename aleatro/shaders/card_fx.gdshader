shader_type canvas_item;

// Edition shimmer and dissolve for cards and charms.
// edition: 0 none, 1 foil, 2 holo, 3 chroma.
uniform int edition = 0;
uniform vec2 size = vec2(100.0, 140.0);
uniform float dissolve : hint_range(0.0, 1.0) = 0.0;
uniform vec4 burn : source_color = vec4(1.0, 0.75, 0.3, 1.0);
uniform float phase = 0.0;

varying vec2 local;

void vertex() {
	local = VERTEX;
}

vec3 hue(float h) {
	return clamp(abs(fract(h + vec3(0.0, 2.0 / 3.0, 1.0 / 3.0)) * 6.0 - 3.0) - 1.0, 0.0, 1.0);
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
