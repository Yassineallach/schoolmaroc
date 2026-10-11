// Painted anime sky: deep zenith, glowing horizon band, crisp sun with halo,
// moon and twinkling stars at night.
shader_type sky;

uniform vec4 top_color : source_color = vec4(0.22, 0.52, 0.95, 1.0);
uniform vec4 horizon_color : source_color = vec4(0.74, 0.90, 1.0, 1.0);
uniform vec4 ground_color : source_color = vec4(0.60, 0.74, 0.86, 1.0);
uniform vec4 glow_color : source_color = vec4(1.0, 0.95, 0.85, 1.0);
uniform float night = 0.0;
uniform float sunset = 0.0;

float hash13(vec3 p) {
	p = fract(p * 0.1031);
	p += dot(p, p.zyx + 31.32);
	return fract((p.x + p.y) * p.z);
}

void sky() {
	vec3 d = EYEDIR;
	float h = d.y;
	vec3 col = mix(horizon_color.rgb, top_color.rgb, smoothstep(-0.02, 0.6, h));
	// soft painted band just above the horizon
	col = mix(col, glow_color.rgb, (1.0 - smoothstep(0.0, 0.22, abs(h - 0.03))) * (0.25 + sunset * 0.45));
	if (h < 0.0) {
		col = mix(horizon_color.rgb, ground_color.rgb, smoothstep(0.0, -0.25, h));
	}
	if (LIGHT0_ENABLED) {
		float sd = dot(d, LIGHT0_DIRECTION);
		vec3 lcol = LIGHT0_COLOR;
		float disc = smoothstep(0.9992, 0.9995, sd);
		float halo = pow(max(sd, 0.0), 48.0) * 0.45 + pow(max(sd, 0.0), 6.0) * 0.12 * (1.0 - night);
		col += mix(vec3(1.0, 0.97, 0.88), lcol, 0.4) * (disc * 1.6 + halo);
	}
	// stars
	if (night > 0.01 && h > 0.0) {
		vec3 cell = floor(d * 140.0);
		float s = hash13(cell);
		float star = step(0.9965, s) * (0.6 + 0.4 * sin(TIME * (2.0 + s * 5.0) + s * 60.0));
		col += vec3(1.0, 0.96, 0.85) * star * night * smoothstep(0.05, 0.3, h);
	}
	COLOR = col;
}
