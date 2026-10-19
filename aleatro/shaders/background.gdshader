shader_type canvas_item;

uniform vec4 base_a : source_color = vec4(0.09, 0.30, 0.22, 1.0);
uniform vec4 base_b : source_color = vec4(0.04, 0.15, 0.12, 1.0);
uniform vec4 accent : source_color = vec4(0.85, 0.65, 0.25, 1.0);
uniform float aspect = 0.5625;

void fragment() {
	vec2 uv = UV - 0.5;
	uv.x *= aspect;
	float t = TIME * 0.12;
	float r = length(uv);
	float a = atan(uv.y, uv.x);
	float w = sin(a * 2.0 + r * 9.0 - t * 5.0)
		+ 0.6 * sin(uv.x * 7.0 + t * 1.7) * cos(uv.y * 6.0 - t * 1.1);
	float k = smoothstep(-1.2, 1.4, w);
	vec3 col = mix(base_b.rgb, base_a.rgb, k);
	col = mix(col, accent.rgb, smoothstep(1.15, 1.55, w) * 0.18);
	col *= 1.0 - r * 0.55;
	col = floor(col * 28.0) / 28.0;
	COLOR = vec4(col, 1.0);
}
