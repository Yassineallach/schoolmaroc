shader_type canvas_item;

// Balatro's splash.fs, ported: the smoky swirl behind the startup splash
// (blue and white, vort_speed 1) and behind the title (red and blue, 0.4).
// It starts black and the smoke fades in over the first few seconds;
// mid_flash washes it toward white (the title's fade in after the splash).

uniform float time = 0.0;
uniform float vort_speed = 1.0;
uniform vec4 colour_1 : source_color = vec4(0.0, 0.616, 1.0, 1.0);
uniform vec4 colour_2 : source_color = vec4(1.0);
uniform float mid_flash = 0.0;
uniform float vort_offset = 0.0;

const float PIXEL_SIZE_FAC = 700.0;
const vec4 BLACK = 0.6 * vec4(79.0 / 255.0, 99.0 / 255.0, 103.0 / 255.0, 1.0 / 0.6);

void fragment() {
	vec2 screen = 1.0 / SCREEN_PIXEL_SIZE;
	// pixel coords, floored for the pixel look, centred and scaled by the diagonal
	float pixel_size = length(screen) / PIXEL_SIZE_FAC;
	vec2 uv = (floor(FRAGCOORD.xy / pixel_size) * pixel_size - 0.5 * screen) / length(screen);
	float uv_len = length(uv);

	// a centre swirl that winds up with time
	float speed = time * vort_speed;
	float new_pixel_angle = atan(uv.y, uv.x) + (2.2 + 0.4 * min(6.0, speed)) * uv_len - 1.0 - speed * 0.05 - min(6.0, speed) * speed * 0.02 + vort_offset;
	vec2 mid = (screen / length(screen)) / 2.0;
	vec2 sv = vec2(uv_len * cos(new_pixel_angle) + mid.x, uv_len * sin(new_pixel_angle) + mid.y) - mid;

	// smoke over the swirled coordinates
	sv *= 30.0;
	speed = time * 6.0 * vort_speed + vort_offset + 1033.0;
	vec2 uv2 = vec2(sv.x + sv.y);
	for (int i = 0; i < 5; i++) {
		uv2 += sin(max(sv.x, sv.y)) + sv;
		sv += 0.5 * vec2(cos(5.1123314 + 0.353 * uv2.y + speed * 0.131121), sin(uv2.x - 0.113 * speed));
		sv -= 1.0 * cos(sv.x + sv.y) - 1.0 * sin(sv.x * 0.711 - sv.y);
	}

	// smoke from 0 to 2: near 1 is colour_1, near 0 colour_2, between them black
	float smoke_res = min(2.0, max(-2.0, 1.5 + length(sv) * 0.12 - 0.17 * min(10.0, time * 1.2 - 4.0)));
	if (smoke_res < 0.2) {
		smoke_res = (smoke_res - 0.2) * 0.6 + 0.2;
	}
	float c1p = max(0.0, 1.0 - 2.0 * abs(1.0 - smoke_res));
	float c2p = max(0.0, 1.0 - 2.0 * smoke_res);
	float cb = 1.0 - min(1.0, c1p + c2p);

	vec4 ret_col = colour_1 * c1p + colour_2 * c2p + vec4(cb * BLACK.rgb, cb * colour_1.a);
	float mod_flash = max(mid_flash * 0.8, max(c1p, c2p) * 5.0 - 4.4) + mid_flash * max(c1p, c2p);
	COLOR = clamp(ret_col * (1.0 - mod_flash) + mod_flash * vec4(1.0), 0.0, 1.0);
}
