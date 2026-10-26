shader_type canvas_item;

// Balatro's vortex.fs, ported: the cards flying into the startup splash are
// twisted about the middle of the screen, harder and wider as vortex_amt
// (seconds since the vortex began) grows. Done on the vertices, in screen
// space, like the LÖVE original.

uniform float vortex_amt = 0.0;

void vertex() {
	mat4 to_clip = SCREEN_MATRIX * CANVAS_MATRIX * MODEL_MATRIX;
	vec4 cp = to_clip * vec4(VERTEX, 0.0, 1.0);
	vec2 screen = vec2(2.0 / SCREEN_MATRIX[0][0], 2.0 / abs(SCREEN_MATRIX[1][1]));
	float diag = length(screen);
	// LÖVE's pixel position relative to the centre (y down), over the diagonal
	vec2 uv = vec2(cp.x, -cp.y) * 0.5 * screen / diag;

	float effect_radius = 1.6 - 0.05 * vortex_amt;
	float effect_angle = 0.5 + 0.15 * vortex_amt;
	float len = length(uv * vec2(screen.x / screen.y, 1.0));
	float angle = atan(uv.y, uv.x) + effect_angle * smoothstep(effect_radius, 0.0, len);
	float radius = length(uv);

	vec2 moved = vec2(radius * cos(angle), radius * sin(angle)) * diag;
	cp.x = moved.x / (0.5 * screen.x);
	cp.y = -moved.y / (0.5 * screen.y);
	VERTEX = (inverse(to_clip) * cp).xy;
}
