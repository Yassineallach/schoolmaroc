shader_type canvas_item;

// Balatro's booster.fs, ported: the moving sheen drawn as a second layer
// over booster packs and Spectral cards (Card:draw draws the card, then its
// sprite again through this shader). Balatro's booster.r is
// rotation*3 + time/28 + juice + tilt; here it is time/28 + `phase`
// (+ `tilt` from the view). The dissolve part is left out: packs here
// never burn away through it.

uniform float phase = 0.0;
uniform float tilt = 0.0;

void fragment() {
	vec4 tex = texture(TEXTURE, UV);
	vec2 uv = UV;
	float r = TIME / 28.0 + phase + tilt;

	float low = min(tex.r, min(tex.g, tex.b));
	float high = max(tex.r, max(tex.g, tex.b));
	float delta = max(high - low, low * 0.7);

	float fac = 0.8 + 0.9 * sin(13.0 * uv.x + 5.32 * uv.y + r * 12.0 + cos(r * 5.3 + uv.y * 4.2 - uv.x * 4.0));
	float fac2 = 0.5 + 0.5 * sin(10.0 * uv.x + 2.32 * uv.y + r * 5.0 - cos(r * 2.3 + uv.x * 8.2));
	float fac3 = 0.5 + 0.5 * sin(12.0 * uv.x + 6.32 * uv.y + r * 6.111 + sin(r * 5.3 + uv.y * 3.2));
	float fac4 = 0.5 + 0.5 * sin(4.0 * uv.x + 2.32 * uv.y + r * 8.111 + sin(r * 1.3 + uv.y * 13.2));
	float fac5 = sin(0.5 * 16.0 * uv.x + 5.32 * uv.y + r * 12.0 + cos(r * 5.3 + uv.y * 4.2 - uv.x * 4.0));

	float maxfac = 0.6 * max(max(fac, max(fac2, max(fac3, 0.0))) + (fac + fac2 + fac3 * fac4), 0.0);

	tex.rgb = tex.rgb * 0.5 + vec3(0.4, 0.4, 0.8);
	tex.r = tex.r - delta + delta * maxfac * (0.7 + fac5 * 0.07) - 0.1;
	tex.g = tex.g - delta + delta * maxfac * (0.7 - fac5 * 0.17) - 0.1;
	tex.b = tex.b - delta + delta * maxfac * 0.7 - 0.1;
	tex.a = tex.a * (0.8 * max(min(1.0, max(0.0, 0.3 * max(low * 0.2, delta) + min(max(maxfac * 0.1, 0.0), 0.4))), 0.0) + 0.15 * maxfac * (0.1 + delta));

	COLOR = tex * COLOR;
}
