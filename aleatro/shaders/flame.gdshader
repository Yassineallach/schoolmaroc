shader_type canvas_item;

// Balatro's flame.fs, ported: the pixel flames that rise from the Chips and
// Mult boxes once a hand's score beats the blind. amount = intensity
// (0 = none, up to 10), id = a per-flame seed, time = the flame's own clock.

uniform float time = 0.0;
uniform float amount = 0.0;
uniform vec4 colour_1 : source_color = vec4(0.086, 0.580, 0.533, 1.0);
uniform vec4 colour_2 : source_color = vec4(1.0, 1.0, 0.5, 1.0);
uniform float id = 0.0;

const float PIXEL_SIZE_FAC = 60.0;

void fragment() {
	float intensity = min(10.0, amount);
	if (intensity < 0.1) {
		COLOR = vec4(0.0);
	} else {
		vec2 uv = UV - 0.5;
		vec2 floored_uv = floor(uv * PIXEL_SIZE_FAC) / PIXEL_SIZE_FAC;
		vec2 c = floored_uv;
		c += c * 0.01 * (sin(-1.123 * floored_uv.x + 0.2 * time) * cos(5.3332 * floored_uv.y + time * 0.931));
		vec2 flame_up_vec = vec2(0.0, mod(4.0 * time, 10000.0) - 5000.0 + mod(1.781 * id, 1000.0));

		float scale_fac = 7.5 + 3.0 / (2.0 + 2.0 * intensity);
		vec2 sv = c * scale_fac + flame_up_vec;
		float speed = mod(20.781 * id, 100.0) + 1.0 * sin(time + id) * cos(time * 0.151 + id);
		vec2 sv2 = vec2(0.0);
		for (int i = 0; i < 5; i++) {
			sv2 += sv + 0.05 * sv2.yx * (mod(float(i), 2.0) > 1.0 ? -1.0 : 1.0)
				+ 0.3 * (cos(length(sv) * 0.411) + 0.3344 * sin(length(sv)) - 0.23 * cos(length(sv)));
			sv += 0.5 * vec2(
				cos(cos(sv2.y) + speed * 0.0812) * sin(3.22 + sv2.x - speed * 0.1531),
				sin(-sv2.x * 1.21222 + 0.113785 * speed) * cos(sv2.y * 0.91213 - 0.13582 * speed));
		}

		// smoke from 0 to 2: under 1 is flame
		float smoke_res = max(0.0, (length((sv - flame_up_vec) / scale_fac * 5.0) + 0.1 * (length(c) - 0.5)) * (2.0 / (2.0 + intensity * 0.2)));
		smoke_res = smoke_res + max(0.0, 2.0 - 0.3 * intensity) * max(0.0, 2.0 * (c.y - 0.5) * (c.y - 0.5));
		if (abs(uv.x) > 0.4) {
			smoke_res = smoke_res + 10.0 * (abs(uv.x) - 0.4);
		}
		if (length((uv - vec2(0.0, 0.1)) * vec2(0.19, 1.0)) < min(0.1, intensity * 0.5) && smoke_res > 1.0) {
			smoke_res = smoke_res + min(8.5, intensity * 10.0) * (length((uv - vec2(0.0, 0.1)) * vec2(0.19, 1.0)) - 0.1);
		}

		vec4 ret = colour_1;
		if (smoke_res > 1.0) {
			ret.a = 0.0;
		} else {
			if (uv.y < 0.12) {
				ret = ret * (1.0 - 0.5 * (0.12 - uv.y)) + 2.5 * (0.12 - uv.y) * colour_2;
				ret += ret * (-2.0 + 0.5 * intensity * smoke_res) * (0.12 - uv.y);
			}
			ret.a = 1.0;
		}
		COLOR = ret;
	}
}
