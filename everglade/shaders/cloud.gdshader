// Anime cumulus: flat two-tone cel shading tinted by the time of day.
shader_type spatial;
render_mode unshaded, cull_back, shadows_disabled, fog_disabled;

uniform vec4 lit_color : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform vec4 shade_color : source_color = vec4(0.74, 0.80, 0.96, 1.0);
uniform vec3 sun_dir = vec3(0.3, 0.8, 0.2);

varying vec3 v_wn;
varying float v_h;

void vertex() {
	v_wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	v_h = VERTEX.y;
}

void fragment() {
	float ndl = dot(v_wn, normalize(sun_dir));
	float lit = smoothstep(-0.05, 0.05, ndl) * 0.7 + smoothstep(0.55, 0.62, ndl) * 0.3;
	vec3 col = mix(shade_color.rgb, lit_color.rgb, lit);
	col = mix(col * 0.92, col, smoothstep(0.0, 1.2, v_h));
	ALBEDO = col;
}
