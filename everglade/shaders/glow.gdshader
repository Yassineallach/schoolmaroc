// Lamp & window glass: warm and dim by day, glowing at night.
shader_type spatial;
render_mode specular_disabled;

global uniform float night;

uniform float flicker = 1.0;
uniform vec3 tint = vec3(1.0);   // window light colour (paint tool)

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
	// paper by day (shoji, lanterns), warm glow at night; window glass
	// (vertex alpha 0.5) shows a dark interior with a faint sky sheen by day
	float glass = step(0.25, COLOR.a) * (1.0 - step(0.75, COLOR.a));
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 3.0);
	vec3 dark = mix(vec3(0.06, 0.065, 0.08), vec3(0.42, 0.5, 0.6), 0.06 + fres * 0.18);
	vec3 day = mix(COLOR.rgb * 0.95, dark, glass);
	vec3 lit = COLOR.rgb * vec3(1.0, 0.82, 0.55) * tint;
	ALBEDO = mix(day, lit * 0.6, night);
	EMISSION = lit * night * 2.4 * f + COLOR.rgb * 0.08 * (1.0 - night) * (1.0 - glass);
	ROUGHNESS = mix(0.2, 0.35, glass);
	SPECULAR = mix(0.6, 0.08, glass);
}
