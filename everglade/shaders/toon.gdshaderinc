// Shared cel-shading model (anime look): two crisp light bands, crisp shadow
// edge, and a thin rim highlight. The shadow side colour comes from the
// (blue-violet) ambient light set by DayCycle, which gives the painted look.
global uniform float toon_rim;

void light() {
	float ndl = dot(NORMAL, LIGHT);
	float wrap = (ndl + 0.2) / 1.2;
	float band = smoothstep(0.0, 0.05, wrap) * 0.78 + smoothstep(0.5, 0.55, wrap) * 0.22;
	float shadow = smoothstep(0.25, 0.55, ATTENUATION);
	float lit = band * shadow;
	vec3 lc = LIGHT_COLOR / PI;
	DIFFUSE_LIGHT += lc * lit;
	float rim = 1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0);
	rim = smoothstep(0.62, 0.68, rim) * lit * toon_rim;
	SPECULAR_LIGHT += lc * ALBEDO * rim * 0.9;
}
