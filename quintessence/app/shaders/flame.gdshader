shader_type canvas_item;
// Candle flame. Height grows with Insight / target. Gutter bends it sideways.
uniform float height = 0.5;   // 0..1
uniform float gutter = 0.0;   // 0..1
uniform float flare = 0.0;    // 0..1

void fragment() {
	vec2 uv = UV;                       // 0..1, origin top-left
	float y = 1.0 - uv.y;               // 0 at wick, 1 at top of rect
	float h = mix(0.28, 0.95, clamp(height, 0.0, 1.0)) * (1.0 + 0.25 * flare);
	float sway = sin(TIME * 9.0 + y * 6.0) * 0.025 * y + sin(TIME * 3.1) * 0.015 * y;
	sway += gutter * (0.22 * y * y) * (0.8 + 0.2 * sin(TIME * 31.0));
	float x = (uv.x - 0.5 - sway) * 2.0;
	float yy = y / h;
	// Teardrop: wide near the bottom, pointed at the top.
	float w = 0.42 * sqrt(max(0.0, yy)) * (1.0 - yy) * 2.2;
	float body = smoothstep(w, w * 0.55, abs(x)) * step(0.0, yy) * step(yy, 1.0);
	float core = smoothstep(w * 0.55, w * 0.1, abs(x)) * smoothstep(0.75, 0.15, yy);
	vec3 outer = vec3(1.0, 0.55, 0.16);
	vec3 inner = vec3(1.0, 0.93, 0.72);
	vec3 col = mix(outer, inner, core);
	col = mix(col, vec3(0.35, 0.45, 0.9), smoothstep(0.12, 0.0, yy) * 0.6);
	float glow = exp(-6.0 * length(vec2(x * 0.6, (yy - 0.35) * 0.8))) * 0.35 * (1.0 + flare);
	COLOR = vec4(col + glow * vec3(1.0, 0.7, 0.3), clamp(body + glow, 0.0, 1.0));
}
