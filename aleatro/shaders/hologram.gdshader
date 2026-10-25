shader_type canvas_item;

// Balatro's hologram.fs, ported: the Hologram charm's figure drawn as a
// projection floating over its card. Solid pixels vanish, see-through ones
// keep their colour, a green glow gathers around the figure's edges, and
// rows of the image jitter sideways like a bad signal.

// where this sprite would sit in Balatro's joker atlas (Hologram is row 12
// of 16), so the glitch rows fall as they do there
const float ATLAS_ROW = 12.0;
const float ATLAS_ROWS = 16.0;
const float ATLAS_COLS = 10.0;
// one sample step of the glow, in card widths and heights (0.0015 of the atlas)
const vec2 GLOW_STEP = vec2(0.0015 * ATLAS_COLS, 0.0015 * ATLAS_ROWS);

uniform float spin = 0.0;  // the card's extra spin, added to the clock

void fragment() {
	vec2 hologram = vec2(min(spin * 3.0, 1.0) + TIME / 28.0, TIME);
	vec2 tc = UV;

	// glow: the mean alpha of the not-quite-solid pixels around this one
	float glow = 0.0;
	int samples = 0;
	for (int i = -4; i <= 4; ++i) {
		for (int j = -4; j <= 4; ++j) {
			float a = texture(TEXTURE, tc + GLOW_STEP * vec2(float(i), float(j))).a;
			if (a < 0.9) {
				samples += 1;
				glow += a;
			}
		}
	}
	glow = samples > 0 ? glow / (0.7 * float(samples)) : 0.0;

	// horizontal glitch: two sums of drifting waves down the rows
	float ty = (ATLAS_ROW + tc.y) / ATLAS_ROWS;
	float timefac = hologram.g;
	float offset_l = -10.0 * (-0.5 + sin(timefac * 0.512 + ty * 14.0)
			+ sin(-timefac * 0.8233 + ty * 11.532)
			+ sin(timefac * 0.333 + ty * 13.3)
			+ sin(-timefac * 0.1112331 + ty * 4.044343));
	float offset_r = -10.0 * (-0.5 + sin(timefac * 0.6924 + ty * 19.0)
			+ sin(-timefac * 0.9661 + ty * 21.532)
			+ sin(timefac * 0.4423 + ty * 30.3)
			+ sin(-timefac * 0.13321312 + ty * 3.011));
	if (offset_r >= 1.5 || offset_r <= 0.0) { offset_r = 0.0; }
	if (offset_l >= 1.5 || offset_l <= 0.0) { offset_l = 0.0; }
	tc.x = tc.x + 0.002 * ATLAS_COLS * (-offset_l + offset_r);

	vec4 tex = texture(TEXTURE, tc);
	if (tex.a > 0.999) { tex = vec4(0.0); }
	if (tex.a < 0.001) { tex.rgb = vec3(0.0, 1.0, 1.0); }

	if (tc.x > 0.95 || tc.x < 0.05 || tc.y > 0.95 || tc.y < 0.05) {
		COLOR = vec4(0.0);
	} else {
		float light_strength = 0.4 * (0.3 * sin(2.0 * hologram.g) + 0.6 + 0.3 * sin(hologram.r * 3.0) + 0.9);
		float flicker = light_strength * (1.0 + abs(offset_l) + abs(offset_r)) * glow;
		vec4 col = tex * COLOR;
		if (tex.a < 0.001) {
			col += vec4(0.0, 1.0, 0.5, 0.6) * flicker;
		} else {
			col += vec4(0.0, 0.3, 0.2, 0.3) * flicker;
		}
		COLOR = clamp(col, 0.0, 1.0);
	}
}
