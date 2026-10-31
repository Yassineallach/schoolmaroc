shader_type canvas_item;

// Edition shimmer, dissolve and pointer tilt for cards and charms.
// edition: 0 none, 1 foil, 2 holo, 3 chroma.
// tilt: where the pointer sits on the face, -1..1 per axis; tilt_amt eases
// it in and out (Balatro's `hovering`). skew.fs warps the card about it.
uniform int edition = 0;
uniform vec2 size = vec2(100.0, 140.0);
uniform float dissolve : hint_range(0.0, 1.0) = 0.0;
// Balatro's dissolve.fs: burn_colour_1 rims the edge, burn_colour_2 the
// band behind it and tints the card as it goes (alpha 0 = unused)
uniform vec4 burn_colour_1 : source_color = vec4(0.180, 0.141, 0.251, 1.0);
uniform vec4 burn_colour_2 : source_color = vec4(0.941, 0.639, 0.227, 1.0);
uniform float dissolve_seed = 0.0;  // Balatro's per-card `time`
// the sprite's pixel grid the dissolve works on (a Balatro card at 2x)
const vec2 DISSOLVE_PX = vec2(142.0, 190.0);
uniform float phase = 0.0;
uniform vec2 tilt = vec2(0.0);
uniform float tilt_amt = 0.0;
// Balatro's debuff.fs: a dull red veil and a red X over a debuffed card
uniform bool debuff = false;
// Balatro's played.fs: a card already drawn this round, greyed in the deck view
uniform bool played = false;
// the card's rotation in radians, which Balatro adds into its edition sweeps
uniform float rot = 0.0;
// a fixed number per card: Balatro sends each card's shaders a `time` from
// its ID, so no two Holo cards ripple alike
uniform float card_seed = 0.0;

// Balatro units: a card is 2.049 wide (G.CARD_W)
const float CARD_UNITS = 2.049;

varying vec2 local;
// 1 on a seal's pixels, 2 on a Gold seal's: card_view tags the seal draw
// with a blue channel of 254/255 or 253/255 so it can be told apart
varying float seal;

void vertex() {
	local = VERTEX;
	seal = 0.0;
	if (COLOR.r > 0.999 && COLOR.g > 0.999 && COLOR.b < 0.999 && COLOR.b > 0.985) {
		seal = COLOR.b > 0.994 ? 1.0 : 2.0;
		COLOR.b = 1.0;
	}
	if (tilt_amt > 0.0) {
		// Balatro's skew.fs: each vertex's clip w grows by its squared
		// distance from the pointer, so the card bulges away from where it
		// is touched (Godot can't set w here, so the divide is done by hand)
		mat4 to_clip = SCREEN_MATRIX * CANVAS_MATRIX * MODEL_MATRIX;
		vec4 cp = to_clip * vec4(VERTEX, 0.0, 1.0);
		vec2 screen = vec2(2.0 / SCREEN_MATRIX[0][0], 2.0 / abs(SCREEN_MATRIX[1][1]));
		float mid_dist = length(cp.xy * 0.5 * screen) / length(screen);
		vec2 pointer = size * 0.5 + tilt * size * 0.5;
		vec2 mouse_offset = (VERTEX - pointer) / (size.x / CARD_UNITS);
		float scale = 0.2 * (-0.03 - 0.3 * max(0.0, 0.3 - mid_dist))
				* tilt_amt * dot(mouse_offset, mouse_offset) / (2.0 - mid_dist);
		cp.xy /= 1.0 + scale;
		VERTEX = (inverse(to_clip) * cp).xy;
	}
}

// Card:draw's tilt_var.amt, added to the edition clocks: how far the
// pointer sits off the face's falling diagonal, x0.3
float tilt_var_amt() {
	return abs(tilt.x + tilt.y) * 0.5 * 0.3 * tilt_amt;
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

// Balatro's foil.fs, the pass it draws over a Foil card: the card re-tinted
// toward blue, see-through at 30% and solid along the rings and sweeps that
// turn with the clock, the card's tilt and its rotation
vec4 foil_pass(vec4 tex, vec2 uv) {
	vec2 foil = vec2(min(rot * 3.0, 1.0) + TIME / 28.0 + tilt_var_amt(), TIME);
	vec2 adjusted_uv = uv - vec2(0.5);
	adjusted_uv.x = adjusted_uv.x * size.x / size.y;

	float low = min(tex.r, min(tex.g, tex.b));
	float high = max(tex.r, max(tex.g, tex.b));
	float delta = min(high, max(0.5, 1.0 - low));

	float fac = max(min(2.0 * sin((length(90.0 * adjusted_uv) + foil.r * 2.0) + 3.0 * (1.0 + 0.8 * cos(length(113.1121 * adjusted_uv) - foil.r * 3.121))) - 1.0 - max(5.0 - length(90.0 * adjusted_uv), 0.0), 1.0), 0.0);
	vec2 rotater = vec2(cos(foil.r * 0.1221), sin(foil.r * 0.3512));
	float angle = dot(rotater, adjusted_uv) / max(length(rotater) * length(adjusted_uv), 1e-5);
	float fac2 = max(min(5.0 * cos(foil.g * 0.3 + angle * 3.14 * (2.2 + 0.9 * sin(foil.r * 1.65 + 0.2 * foil.g))) - 4.0 - max(2.0 - length(20.0 * adjusted_uv), 0.0), 1.0), 0.0);
	float fac3 = 0.3 * max(min(2.0 * sin(foil.r * 5.0 + uv.x * 3.0 + 3.0 * (1.0 + 0.5 * cos(foil.r * 7.0))) - 1.0, 1.0), -1.0);
	float fac4 = 0.3 * max(min(2.0 * sin(foil.r * 6.66 + uv.y * 3.8 + 3.0 * (1.0 + 0.5 * cos(foil.r * 3.414))) - 1.0, 1.0), -1.0);

	float maxfac = max(max(fac, max(fac2, max(fac3, max(fac4, 0.0)))) + 2.2 * (fac + fac2 + fac3 + fac4), 0.0);

	tex.r = tex.r - delta + delta * maxfac * 0.3;
	tex.g = tex.g - delta + delta * maxfac * 0.3;
	tex.b = tex.b + delta * maxfac * 1.9;
	tex.a = min(tex.a, 0.3 * tex.a + 0.9 * min(0.5, maxfac * 0.1));
	return tex;
}

// Balatro's holo.fs: the card's hue pushed round by a slow drifting field
// and a fine diamond grid, lifted and blue-tinted, blended over the card
vec4 holo_pass(vec4 tex, vec2 uv) {
	vec2 holo = vec2(min(rot * 3.0, 1.0) + TIME / 28.0 + tilt_var_amt(), TIME);
	vec3 hsl = rgb_to_hsl(0.5 * tex.rgb + 0.5 * vec3(0.0, 0.0, 1.0));

	float t = holo.y * 7.221 + card_seed;
	vec2 floored_uv = floor(uv * DISSOLVE_PX) / DISSOLVE_PX;
	vec2 uv_scaled_centered = (floored_uv - 0.5) * 250.0;
	vec2 f1 = uv_scaled_centered + 50.0 * vec2(sin(-t / 143.6340), cos(-t / 99.4324));
	vec2 f2 = uv_scaled_centered + 50.0 * vec2(cos(t / 53.1532), cos(t / 61.4532));
	vec2 f3 = uv_scaled_centered + 50.0 * vec2(sin(-t / 87.53218), sin(-t / 49.0000));
	float field = (1.0 + (cos(length(f1) / 19.483) + sin(length(f2) / 33.155) * cos(f2.y / 15.73)
			+ cos(length(f3) / 27.193) * sin(f3.x / 21.92))) / 2.0;
	float res = 0.5 + 0.5 * cos(holo.x * 2.612 + (field - 0.5) * 3.14);

	float low = min(tex.r, min(tex.g, tex.b));
	float high = max(tex.r, max(tex.g, tex.b));
	float delta = 0.2 + 0.3 * (high - low) + 0.1 * high;

	float gridsize = 0.79;
	float fac = 0.5 * max(max(max(0.0, 7.0 * abs(cos(uv.x * gridsize * 20.0)) - 6.0),
			max(0.0, 7.0 * cos(uv.y * gridsize * 45.0 + uv.x * gridsize * 20.0) - 6.0)),
			max(0.0, 7.0 * cos(uv.y * gridsize * 45.0 - uv.x * gridsize * 20.0) - 6.0));

	hsl.x = hsl.x + res + fac;
	hsl.y = hsl.y * 1.3;
	hsl.z = hsl.z * 0.6 + 0.4;

	tex = (1.0 - delta) * tex + delta * vec4(hsl_to_rgb(hsl), tex.a) * vec4(0.9, 0.8, 1.2, tex.a);
	if (tex.a < 0.7) {
		tex.a = tex.a / 3.0;
	}
	return tex;
}

// Balatro's negative_shine.fs, the pass it lays over a Negative card: the
// original colours pushed toward lavender, see-through except where waves
// of light roll across, tinted red and green as they pass
vec4 negative_shine_pass(vec4 tex, vec2 uv) {
	float r = min(rot * 3.0, 1.0) + TIME / 28.0 + tilt_var_amt();
	float low = min(tex.r, min(tex.g, tex.b));
	float high = max(tex.r, max(tex.g, tex.b));
	float delta = high - low - 0.1;

	float fac = 0.8 + 0.9 * sin(11.0 * uv.x + 4.32 * uv.y + r * 12.0 + cos(r * 5.3 + uv.y * 4.2 - uv.x * 4.0));
	float fac2 = 0.5 + 0.5 * sin(8.0 * uv.x + 2.32 * uv.y + r * 5.0 - cos(r * 2.3 + uv.x * 8.2));
	float fac3 = 0.5 + 0.5 * sin(10.0 * uv.x + 5.32 * uv.y + r * 6.111 + sin(r * 5.3 + uv.y * 3.2));
	float fac4 = 0.5 + 0.5 * sin(3.0 * uv.x + 2.32 * uv.y + r * 8.111 + sin(r * 1.3 + uv.y * 11.2));
	float fac5 = sin(0.9 * 16.0 * uv.x + 5.32 * uv.y + r * 12.0 + cos(r * 5.3 + uv.y * 4.2 - uv.x * 4.0));

	float maxfac = 0.7 * max(max(fac, max(fac2, max(fac3, 0.0))) + (fac + fac2 + fac3 * fac4), 0.0);

	tex.rgb = tex.rgb * 0.5 + vec3(0.4, 0.4, 0.8);

	tex.r = tex.r - delta + delta * maxfac * (0.7 + fac5 * 0.27) - 0.1;
	tex.g = tex.g - delta + delta * maxfac * (0.7 - fac5 * 0.27) - 0.1;
	tex.b = tex.b - delta + delta * maxfac * 0.7 - 0.1;
	tex.a = tex.a * (0.5 * max(min(1.0, max(0.0, 0.3 * max(low * 0.2, delta) + min(max(maxfac * 0.1, 0.0), 0.4))), 0.0) + 0.15 * maxfac * (0.1 + delta));
	return tex;
}

// Balatro's polychrome.fs (Chroma here), drawn in place of the card: each
// pixel's hue pushed round by a slow drifting field and its saturation
// lifted, so the card washes through the rainbow
vec4 polychrome_pass(vec4 tex, vec2 uv) {
	vec2 polychrome = vec2(min(rot * 3.0, 1.0) + TIME / 28.0 + tilt_var_amt(), TIME);
	float low = min(tex.r, min(tex.g, tex.b));
	float high = max(tex.r, max(tex.g, tex.b));
	float delta = high - low;
	float saturation_fac = 1.0 - max(0.0, 0.05 * (1.1 - delta));
	vec3 hsl = rgb_to_hsl(vec3(tex.r * saturation_fac, tex.g * saturation_fac, tex.b));

	float t = polychrome.y * 2.221 + card_seed;
	vec2 floored_uv = floor(uv * DISSOLVE_PX) / DISSOLVE_PX;
	vec2 uv_scaled_centered = (floored_uv - 0.5) * 50.0;
	vec2 f1 = uv_scaled_centered + 50.0 * vec2(sin(-t / 143.6340), cos(-t / 99.4324));
	vec2 f2 = uv_scaled_centered + 50.0 * vec2(cos(t / 53.1532), cos(t / 61.4532));
	vec2 f3 = uv_scaled_centered + 50.0 * vec2(sin(-t / 87.53218), sin(-t / 49.0000));
	float field = (1.0 + (cos(length(f1) / 19.483) + sin(length(f2) / 33.155) * cos(f2.y / 15.73)
			+ cos(length(f3) / 27.193) * sin(f3.x / 21.92))) / 2.0;
	float res = 0.5 + 0.5 * cos(polychrome.x * 2.612 + (field - 0.5) * 3.14);
	hsl.x = hsl.x + res + polychrome.y * 0.04;
	hsl.y = min(0.6, hsl.y + 0.5);

	tex.rgb = hsl_to_rgb(hsl);
	if (tex.a < 0.7) {
		tex.a = tex.a / 3.0;
	}
	return tex;
}

// Balatro's voucher.fs, the shine Card:draw lays over a Gold seal (and
// over vouchers, in voucher.gdshader): the seal pushed toward lavender,
// see-through except where waves of light roll across
vec4 voucher_pass(vec4 tex, vec2 uv, float r) {
	float low = min(tex.r, min(tex.g, tex.b));
	float high = max(tex.r, max(tex.g, tex.b));
	float delta = high - low;

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
	return tex;
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
	if (seal > 1.5) {
		// the timer Balatro sends its card shaders (Card:draw's send_to_shader)
		vec4 v = voucher_pass(c, UV, min(rot * 3.0, 1.0) + TIME / 28.0 + tilt_var_amt());
		c.rgb = mix(c.rgb, clamp(v.rgb, 0.0, 1.0), clamp(v.a, 0.0, 1.0));
	}
	// editions shine on the card, not on the seal drawn over it
	int ed = seal > 0.5 ? 0 : edition;
	if (ed == 1) {
		vec4 f = foil_pass(c, uv);
		c.rgb = mix(c.rgb, clamp(f.rgb, 0.0, 1.0), clamp(f.a, 0.0, 1.0) * face);
	} else if (ed == 2) {
		vec4 h = holo_pass(c, uv);
		c.rgb = mix(c.rgb, clamp(h.rgb, 0.0, 1.0), clamp(h.a, 0.0, 1.0) * face);
	} else if (ed == 3) {
		c.rgb = mix(c.rgb, polychrome_pass(c, uv).rgb, face);
	} else if (ed == 4) {
		// Balatro's negative.fs, drawn in place of the card: lightness
		// flipped, hue mirrored about 0.2, and a slate grey added on top
		vec3 sat = rgb_to_hsl(c.rgb);
		sat.z = 1.0 - sat.z;
		sat.x = -sat.x + 0.2;
		vec3 neg = hsl_to_rgb(vec3(fract(sat.x), sat.y, sat.z)) + 0.8 * vec3(79.0, 99.0, 103.0) / 255.0;
		vec4 shine = negative_shine_pass(c, uv);
		neg = mix(clamp(neg, 0.0, 1.0), clamp(shine.rgb, 0.0, 1.0), clamp(shine.a, 0.0, 1.0));
		c.rgb = mix(c.rgb, neg, face);
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
	if (played) {
		// played.fs, drawn in place of the card: half the saturation, 80%
		// of the lightness, half see-through
		vec3 hsl = rgb_to_hsl(c.rgb);
		hsl.y *= 0.5;
		hsl.z *= 0.8;
		c = vec4(hsl_to_rgb(hsl), c.a * 0.5);
	}
	if (dissolve > 0.001) {
		// dissolve.fs: tint toward the burn colour, then a drifting field,
		// pulled down near the edges, eats the card from the outside in
		if (burn_colour_2.a > 0.01) {
			c.rgb = mix(c.rgb, c.rgb * (1.0 - 0.6 * dissolve) + 0.6 * burn_colour_2.rgb * dissolve, face);
		} else if (burn_colour_1.a > 0.01) {
			c.rgb = mix(c.rgb, c.rgb * (1.0 - 0.6 * dissolve) + 0.6 * burn_colour_1.rgb * dissolve, face);
		}
		float adjusted = (dissolve * dissolve * (3.0 - 2.0 * dissolve)) * 1.02 - 0.01;
		float t = dissolve_seed * 10.0 + 2003.0;
		float px = max(DISSOLVE_PX.x, DISSOLVE_PX.y);
		vec2 floored_uv = floor(uv * DISSOLVE_PX) / px;
		vec2 centred = (floored_uv - 0.5) * 2.3 * px;
		vec2 f1 = centred + 50.0 * vec2(sin(-t / 143.6340), cos(-t / 99.4324));
		vec2 f2 = centred + 50.0 * vec2(cos(t / 53.1532), cos(t / 61.4532));
		vec2 f3 = centred + 50.0 * vec2(sin(-t / 87.53218), sin(-t / 49.0000));
		float field = (1.0 + (cos(length(f1) / 19.483) + sin(length(f2) / 33.155) * cos(f2.y / 15.73)
				+ cos(length(f3) / 27.193) * sin(f3.x / 21.92))) / 2.0;
		vec2 borders = vec2(0.2, 0.8);
		float res = (0.5 + 0.5 * cos(adjusted / 82.612 + (field - 0.5) * 3.14))
			- (floored_uv.x > borders.y ? (floored_uv.x - borders.y) * (5.0 + 5.0 * dissolve) : 0.0) * dissolve
			- (floored_uv.y > borders.y ? (floored_uv.y - borders.y) * (5.0 + 5.0 * dissolve) : 0.0) * dissolve
			- (floored_uv.x < borders.x ? (borders.x - floored_uv.x) * (5.0 + 5.0 * dissolve) : 0.0) * dissolve
			- (floored_uv.y < borders.x ? (borders.x - floored_uv.y) * (5.0 + 5.0 * dissolve) : 0.0) * dissolve;
		if (face > 0.5 && burn_colour_1.a > 0.01 && res > adjusted && res < adjusted + 0.8 * (0.5 - abs(adjusted - 0.5))) {
			if (res < adjusted + 0.5 * (0.5 - abs(adjusted - 0.5))) {
				c.rgb = burn_colour_1.rgb;
			} else if (burn_colour_2.a > 0.01) {
				c.rgb = burn_colour_2.rgb;
			}
		}
		if (res <= adjusted) {
			discard;
		}
	}
	COLOR = c;
}
