shader_type canvas_item;
// Wall (top) and velvet table cloth. Lighting is applied later by darkness.gdshader.
uniform vec2 size = vec2(720.0, 1280.0);
uniform float wall_y = 300.0;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x),
		mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}

void fragment() {
	vec2 px = UV * size;
	vec3 col;
	if (px.y < wall_y) {
		// Faded damask wallpaper: vertical bands + soft lozenge pattern.
		vec3 base = vec3(0.16, 0.12, 0.10);
		float band = 0.5 + 0.5 * sin(px.x * 0.105);
		vec2 q = vec2(px.x / 46.0, px.y / 62.0);
		vec2 g = fract(q + vec2(0.5 * floor(q.y), 0.0)) - 0.5;
		float lozenge = smoothstep(0.32, 0.28, abs(g.x) + abs(g.y) * 0.8);
		col = base * (0.86 + 0.08 * band + 0.10 * lozenge) * (0.9 + 0.2 * noise(px * 0.05));
		// Wainscot rail at the table edge.
		float rail = smoothstep(wall_y - 18.0, wall_y - 14.0, px.y);
		col = mix(col, vec3(0.10, 0.07, 0.05), rail);
		col += vec3(0.08, 0.05, 0.02) * smoothstep(wall_y - 15.0, wall_y - 13.0, px.y) * (1.0 - smoothstep(wall_y - 13.0, wall_y - 10.0, px.y));
	} else {
		// Velvet: dark wine-brown cloth with soft folds and fine pile.
		vec3 cloth = vec3(0.165, 0.11, 0.086);
		float folds = noise(vec2(px.x * 0.006, px.y * 0.012)) * 0.6 + noise(px * 0.02) * 0.25;
		float pile = hash(floor(px * 0.75)) * 0.06;
		col = cloth * (0.82 + 0.3 * folds) + pile * cloth;
		// Shadow under the table edge.
		col *= 0.55 + 0.45 * smoothstep(wall_y, wall_y + 40.0, px.y);
	}
	COLOR = vec4(col, 1.0);
}
