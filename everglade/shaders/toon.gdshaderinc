// Shared stylised lighting: soft cel bands (three steps with painterly,
// widened transitions so surface detail and normal maps read), a crisp
// shadow edge, a glossy highlight driven by the material roughness/metalness
// and a thin rim light. The shadow side colour comes from the blue-violet
// ambient set by DayCycle.
global uniform float toon_rim;

void light() {
	float ndl = dot(NORMAL, LIGHT);
	float wrap = (ndl + 0.2) / 1.2;
	float band = smoothstep(-0.02, 0.12, wrap) * 0.74 + smoothstep(0.3, 0.52, wrap) * 0.18 + smoothstep(0.7, 0.92, wrap) * 0.08;
	float shadow = smoothstep(0.25, 0.55, ATTENUATION);
	float lit = band * shadow;
	vec3 lc = LIGHT_COLOR / PI;
	DIFFUSE_LIGHT += lc * lit;
	// stylised specular: tight and bright on metal, broad and faint on stone
	vec3 h = normalize(LIGHT + VIEW);
	float gloss = clamp(1.0 - ROUGHNESS, 0.0, 1.0);
	float sp = pow(max(dot(NORMAL, h), 0.0), mix(6.0, 90.0, gloss));
	sp = smoothstep(0.25, 0.75, sp) * gloss * gloss * shadow * step(0.0, ndl);
	SPECULAR_LIGHT += lc * sp * mix(vec3(0.5), ALBEDO * 2.2, METALLIC);
	float rim = 1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0);
	rim = smoothstep(0.62, 0.68, rim) * lit * toon_rim;
	SPECULAR_LIGHT += lc * ALBEDO * rim * 0.9;
}
