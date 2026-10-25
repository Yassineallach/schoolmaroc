shader_type canvas_item;

// Balatro's flash.fs, ported: the white that swells out from the middle of
// the screen at the end of the startup splash. time = seconds since the
// splash began; mid_flash scales the whole flash (1 during the splash, then
// 1.6 eased to 0 as the title appears).

uniform float time = 0.0;
uniform float mid_flash = 1.0;

const float PIXEL_SIZE_FAC = 700.0;

void fragment() {
	vec2 screen = 1.0 / SCREEN_PIXEL_SIZE;
	// pixel coords, floored for the pixel look, then centred and scaled by the diagonal
	float pixel_size = length(screen) / PIXEL_SIZE_FAC;
	vec2 uv = (floor(FRAGCOORD.xy / pixel_size) * pixel_size - 0.5 * screen) / length(screen);

	float mid_white = min(1.0, (time > 2.5 ? max(0.0, sqrt(time - 2.5) - 60.0 * length(uv)) : 0.0)
		+ (time > 11.0 ? max(0.0, (time - 11.0) * (time - 11.0) - 5.0 * length(uv)) : 0.0));

	COLOR = vec4(1.0, 1.0, 1.0, mid_flash * mid_white);
}
