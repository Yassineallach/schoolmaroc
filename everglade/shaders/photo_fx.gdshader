// Photo-mode finishing pass, drawn over the finished frame (so water and
// everything else is already in it): exposure, saturation, a colour filter,
// a vignette and an optional painterly (Kuwahara) look.
shader_type canvas_item;

uniform sampler2D screen_tex : hint_screen_texture, filter_linear_mipmap;
uniform float exposure = 1.0;
uniform float saturation = 1.0;
uniform float vignette = 0.3;
uniform int filter_mode = 0;   // 0 none, 1 warm, 2 cool, 3 sepia, 4 mono, 5 dreamy
uniform float paint = 0.0;     // 0 off, 1 painterly

vec3 kuwahara(vec2 uv, vec2 px) {
	vec3 mean[4];
	float var_[4];
	int r = 3;
	for (int q = 0; q < 4; q++) {
		vec2 dir = vec2(q % 2 == 0 ? -1.0 : 1.0, q < 2 ? -1.0 : 1.0);
		vec3 sum = vec3(0.0);
		vec3 sum2 = vec3(0.0);
		float n = 0.0;
		for (int i = 0; i <= r; i++) {
			for (int j = 0; j <= r; j++) {
				vec3 c = texture(screen_tex, uv + dir * vec2(float(i), float(j)) * px * 1.5).rgb;
				sum += c;
				sum2 += c * c;
				n += 1.0;
			}
		}
		mean[q] = sum / n;
		vec3 v = sum2 / n - mean[q] * mean[q];
		var_[q] = v.r + v.g + v.b;
	}
	vec3 best = mean[0];
	float bv = var_[0];
	for (int q = 1; q < 4; q++) {
		if (var_[q] < bv) {
			bv = var_[q];
			best = mean[q];
		}
	}
	return best;
}

void fragment() {
	vec2 uv = SCREEN_UV;
	vec3 c = texture(screen_tex, uv).rgb;
	if (paint > 0.5) {
		c = kuwahara(uv, SCREEN_PIXEL_SIZE);
	}
	c *= exposure;
	float lum = dot(c, vec3(0.299, 0.587, 0.114));
	c = mix(vec3(lum), c, saturation);
	if (filter_mode == 1) {
		c *= vec3(1.08, 0.98, 0.86);
	} else if (filter_mode == 2) {
		c *= vec3(0.88, 0.98, 1.1);
	} else if (filter_mode == 3) {
		c = vec3(lum) * vec3(1.1, 0.94, 0.74);
	} else if (filter_mode == 4) {
		c = vec3(lum);
	} else if (filter_mode == 5) {
		vec3 soft = textureLod(screen_tex, uv, 3.0).rgb;
		c = mix(c, max(c, soft), 0.45) * vec3(1.03, 1.0, 1.04);
	}
	vec2 d = uv - 0.5;
	float v = smoothstep(0.85, 0.2, length(d * vec2(1.25, 1.0)));
	c *= mix(1.0, v, vignette);
	COLOR = vec4(c, 1.0);
}
