shader_type canvas_item;

// Balatro's CRT.fs, ported: drawn over the whole screen last, it bends the
// picture slightly, adds scanlines, a hint of colour fringing, grain and
// (optionally) bloom. Uniforms as Game:draw sends them; see main.gd
// _apply_crt for the values its settings give.

uniform sampler2D screen_tex : hint_screen_texture, filter_linear;
uniform vec2 distortion_fac = vec2(1.0147, 1.021);
uniform vec2 scale_fac = vec2(0.99832, 0.99832);
uniform float feather_fac = 0.01;
uniform float noise_fac = 0.00021;
uniform float bloom_fac = 0.0;
uniform float crt_intensity = 0.0336;
uniform float glitch_intensity = 0.0;
uniform float scanlines = 540.0;

const float BUFF = 0.01;
const int BLOOM_AMT = 3;

void fragment() {
	vec2 screen = 1.0 / SCREEN_PIXEL_SIZE;
	float time = 400.0 + TIME;
	vec2 tc = SCREEN_UV;

	// recentre, then bulge from the middle
	tc = tc * 2.0 - vec2(1.0);
	tc *= scale_fac;
	tc += (tc.yx * tc.yx) * tc * (distortion_fac - 1.0);
	// smooth fade to black at the edge
	float mask = (1.0 - smoothstep(1.0 - feather_fac, 1.0, abs(tc.x) - BUFF))
			* (1.0 - smoothstep(1.0 - feather_fac, 1.0, abs(tc.y) - BUFF));
	tc = (tc + vec2(1.0)) / 2.0;

	// horizontal glitch offsets (Balatro sends 0, so normally off)
	float offset_l = 0.0;
	float offset_r = 0.0;
	if (glitch_intensity > 0.01) {
		float timefac = 3.0 * time;
		offset_l = 50.0 * (-3.5 + sin(timefac * 0.512 + tc.y * 40.0) + sin(-timefac * 0.8233 + tc.y * 81.532)
				+ sin(timefac * 0.333 + tc.y * 30.3) + sin(-timefac * 0.1112331 + tc.y * 13.0));
		offset_r = -50.0 * (-3.5 + sin(timefac * 0.6924 + tc.y * 29.0) + sin(-timefac * 0.9661 + tc.y * 41.532)
				+ sin(timefac * 0.4423 + tc.y * 40.3) + sin(-timefac * 0.13321312 + tc.y * 11.0));
		if (glitch_intensity > 1.0) {
			offset_l = 50.0 * (-1.5 + sin(timefac * 0.512 + tc.y * 4.0) + sin(-timefac * 0.8233 + tc.y * 1.532)
					+ sin(timefac * 0.333 + tc.y * 3.3) + sin(-timefac * 0.1112331 + tc.y * 1.0));
			offset_r = -50.0 * (-1.5 + sin(timefac * 0.6924 + tc.y * 19.0) + sin(-timefac * 0.9661 + tc.y * 21.532)
					+ sin(timefac * 0.4423 + tc.y * 20.3) + sin(-timefac * 0.13321312 + tc.y * 5.0));
		}
		tc.x = tc.x + 0.001 * glitch_intensity * clamp(offset_l, clamp(offset_r, -1.0, 0.0), 1.0);
	}

	vec4 crt_tex = texture(screen_tex, tc);
	float artifact_amplifier = (abs(clamp(offset_l, clamp(offset_r, -1.0, 0.0), 1.0)) * glitch_intensity > 0.9 ? 3.0 : 1.0);

	// horizontal chromatic aberration
	float crt_amount_adjusted = max(0.0, crt_intensity / (0.16 * 0.3)) * artifact_amplifier;
	if (crt_amount_adjusted > 0.0000001) {
		float shift = 0.0005 * (1.0 + 10.0 * (artifact_amplifier - 1.0)) * 1600.0 / screen.x;
		crt_tex.r = crt_tex.r * (1.0 - crt_amount_adjusted) + crt_amount_adjusted * texture(screen_tex, tc + vec2(shift, 0.0)).r;
		crt_tex.g = crt_tex.g * (1.0 - crt_amount_adjusted) + crt_amount_adjusted * texture(screen_tex, tc + vec2(-shift, 0.0)).g;
	}
	vec3 rgb_result = crt_tex.rgb * (1.0 - crt_intensity * artifact_amplifier);

	// glitch colour bands
	if (sin(time + tc.y * 200.0) > 0.85) {
		if (offset_l < 0.99 && offset_l > 0.01) rgb_result.r = rgb_result.g * 1.5;
		if (offset_r > -0.99 && offset_r < -0.01) rgb_result.g = rgb_result.r * 1.5;
	}

	// the scanline / phosphor overlay
	vec3 rgb_scanline = vec3(
		clamp(-0.3 + 2.0 * sin(tc.y * scanlines - 3.14 / 4.0) - 0.8 * clamp(sin(tc.x * scanlines * 4.0), 0.4, 1.0), -1.0, 2.0),
		clamp(-0.3 + 2.0 * cos(tc.y * scanlines) - 0.8 * clamp(cos(tc.x * scanlines * 4.0), 0.0, 1.0), -1.0, 2.0),
		clamp(-0.3 + 2.0 * cos(tc.y * scanlines - 3.14 / 3.0) - 0.8 * clamp(cos(tc.x * scanlines * 4.0 - 3.14 / 4.0), 0.0, 1.0), -1.0, 2.0));
	rgb_result += crt_tex.rgb * rgb_scanline * crt_intensity * artifact_amplifier;

	// grain
	float x = (tc.x - mod(tc.x, 0.002)) * (tc.y - mod(tc.y, 0.0013)) * time * 1000.0;
	x = mod(x, 13.0) * mod(x, 123.0);
	float dx = mod(x, 0.11) / 0.11;
	float nf = clamp(noise_fac * artifact_amplifier, 0.0, 1.0);
	rgb_result = (1.0 - nf) * rgb_result + dx * nf * vec3(1.0);

	// contrast and brightness, allowing for bloom
	rgb_result -= vec3(0.55 - 0.02 * (artifact_amplifier - 1.0 - crt_amount_adjusted * bloom_fac * 0.7));
	rgb_result = rgb_result * (1.0 + 0.14 + crt_amount_adjusted * (0.012 - bloom_fac * 0.12));
	rgb_result += vec3(0.5);
	vec4 final_col = vec4(rgb_result, 1.0);

	// bloom
	vec4 col = vec4(0.0);
	float bloom = 0.0;
	if (bloom_fac > 0.00001 && crt_intensity > 0.000001) {
		bloom = 0.03 * max(0.0, crt_intensity / (0.16 * 0.3));
		float bloom_dist = 0.0015 * float(BLOOM_AMT);
		float cutoff = 0.6;
		for (int i = -BLOOM_AMT; i <= BLOOM_AMT; ++i) {
			for (int j = -BLOOM_AMT; j <= BLOOM_AMT; ++j) {
				vec4 samp = texture(screen_tex, tc + (bloom_dist / float(BLOOM_AMT)) * vec2(float(i), float(j)));
				samp.r = max(1.0 / (1.0 - cutoff) * samp.r - 1.0 / (1.0 - cutoff) + 1.0, 0.0);
				samp.g = max(1.0 / (1.0 - cutoff) * samp.g - 1.0 / (1.0 - cutoff) + 1.0, 0.0);
				samp.b = max(1.0 / (1.0 - cutoff) * samp.b - 1.0 / (1.0 - cutoff) + 1.0, 0.0);
				col += min(min(samp.r, samp.g), samp.b) * (2.0 - float(abs(float(i + j))) / float(BLOOM_AMT + BLOOM_AMT));
			}
		}
		col /= float(BLOOM_AMT * BLOOM_AMT);
		col.a = final_col.a;
	}

	COLOR = vec4(((final_col * (1.0 - bloom) + bloom * col) * mask).rgb, 1.0);
}
