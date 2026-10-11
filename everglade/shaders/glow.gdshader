// Lamp & window glass: warm and dim by day, glowing at night.
shader_type spatial;
render_mode specular_disabled;

global uniform float night;

uniform float flicker = 1.0;

float hash11(float p) {
	p = fract(p * 0.1031);
	p *= p + 33.33;
	p *= p + p;
	return fract(p);
}

void fragment() {
	vec3 world = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float seed = hash11(floor(world.x * 3.0) + floor(world.z * 3.0) * 57.0);
	float f = 1.0 + flicker * 0.08 * sin(TIME * (6.0 + seed * 5.0) + seed * 40.0);
	// paper by day (shoji, lanterns), warm glow at night
	vec3 day = COLOR.rgb * 0.95;
	vec3 lit = COLOR.rgb * vec3(1.0, 0.82, 0.55);
	ALBEDO = mix(day, lit * 0.6, night);
	EMISSION = lit * night * 2.4 * f + COLOR.rgb * 0.08 * (1.0 - night);
	ROUGHNESS = 0.2;
	SPECULAR = 0.6;
}
