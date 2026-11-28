shader_type canvas_item;
// The candle is the only light. Everything is darkened by distance from the flame.
uniform vec2 size = vec2(720.0, 1280.0);
uniform vec2 candle = vec2(110.0, 470.0);
uniform float radius = 860.0;     // light reach in pixels
uniform float brightness = 0.6;   // 0..1, grows with Insight / target
uniform float gutter = 0.0;       // 0..1, Shadow moment: light shrinks and wavers
uniform float flare = 0.0;        // 0..1, big score: room brightens

void fragment() {
	vec2 px = UV * size;
	vec2 d2 = (px - candle) * vec2(0.62, 0.64);
	float t = TIME;
	float flick = 1.0 + 0.035 * sin(t * 21.0) + 0.025 * sin(t * 33.0 + 1.7) + 0.02 * sin(t * 7.3);
	flick -= gutter * (0.22 + 0.12 * sin(t * 47.0));
	float r = radius * (0.72 + 0.38 * brightness) * flick * (1.0 + 0.35 * flare);
	float d = length(d2) / r;
	vec3 ink = vec3(0.03, 0.022, 0.018);
	vec3 warm = vec3(1.0, 0.72, 0.38);
	float dark = smoothstep(0.3, 1.25, d);
	float a = mix(0.06, 0.9, dark);
	a *= 1.0 - 0.6 * flare;
	vec3 col = mix(warm, ink, smoothstep(0.0, 0.5, d));
	COLOR = vec4(col, a);
}
