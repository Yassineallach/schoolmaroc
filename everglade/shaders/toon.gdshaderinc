// Shared soft natural lighting (handcrafted-diorama look): smooth wrapped
// diffuse with a gentle terminator so curved and bevelled forms read, soft
// shadow edges, and a broad, restrained highlight driven by roughness (matte
// stone barely shines; iron and gold get a small warm glint). Ambient fill
// and contact shading come from DayCycle and the post AO pass.
global uniform float toon_rim;

void light() {
	float ndl = dot(NORMAL, LIGHT);
	float wrap = clamp((ndl + 0.18) / 1.18, 0.0, 1.0);
	float diff = wrap * wrap * (3.0 - 2.0 * wrap);
	diff = mix(wrap, diff, 0.5);
	float shadow = smoothstep(0.05, 0.85, ATTENUATION);
	vec3 lc = LIGHT_COLOR / PI;
	DIFFUSE_LIGHT += lc * diff * shadow;
	vec3 h = normalize(LIGHT + VIEW);
	float gloss = clamp(1.0 - ROUGHNESS, 0.0, 1.0);
	float sp = pow(max(dot(NORMAL, h), 0.0), mix(4.0, 64.0, gloss)) * gloss * gloss;
	SPECULAR_LIGHT += lc * sp * shadow * step(0.0, ndl) * mix(vec3(0.35), ALBEDO * 1.8, METALLIC);
	// optional faint rim (off by default in the natural look)
	float rim = 1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0);
	SPECULAR_LIGHT += lc * ALBEDO * smoothstep(0.6, 0.75, rim) * diff * shadow * toon_rim;
}
