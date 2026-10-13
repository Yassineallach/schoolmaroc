// Shared surface-material library: a 16-slice texture array of tileable
// detail albedo (RGB around mid-grey, A = roughness) and normal maps made by
// tools/gen_materials.py. Slices:
//   0 painted   1 cut stone  2 rock      3 wood planks  4 bark     5 plaster
//   6 tiles     7 cloth      8 metal     9 moss         10 cobbles 11 straw
//   12 meadow  13 dirt      14 flagstone 15 sand
uniform sampler2DArray mat_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2DArray mat_normal : filter_linear_mipmap_anisotropic, repeat_enable;

// texture repeats per metre, normal-map strength, metalness per slice
const float MAT_SCALE[16] = float[16](0.5, 0.55, 0.35, 0.95, 1.1, 0.55, 0.7, 1.4, 1.1, 1.2, 0.8, 1.0, 0.35, 0.5, 0.42, 0.5);
const float MAT_BUMP[16] = float[16](0.35, 1.0, 1.0, 0.8, 1.0, 0.55, 0.9, 0.5, 0.7, 0.8, 1.0, 0.8, 0.7, 0.8, 1.0, 0.6);
const float MAT_METAL[16] = float[16](0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.75, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);

vec3 mat_tangent_normal(vec2 uv, float layer, float bump) {
	vec3 n = texture(mat_normal, vec3(uv, layer)).xyz * 2.0 - 1.0;
	n.xy *= bump;
	return normalize(n);
}

// Triplanar sample in object space (whiteout blend). `p` is already scaled.
// Returns detail albedo and writes the perturbed object-space normal.
vec4 mat_triplanar(vec3 p, vec3 n, float layer, float bump, out vec3 nrm) {
	vec3 w = pow(abs(n), vec3(4.0));
	w /= (w.x + w.y + w.z);
	vec4 alb = texture(mat_albedo, vec3(p.zy, layer)) * w.x
			+ texture(mat_albedo, vec3(p.xz, layer)) * w.y
			+ texture(mat_albedo, vec3(p.xy, layer)) * w.z;
	vec3 tx = texture(mat_normal, vec3(p.zy, layer)).xyz * 2.0 - 1.0;
	vec3 ty = texture(mat_normal, vec3(p.xz, layer)).xyz * 2.0 - 1.0;
	vec3 tz = texture(mat_normal, vec3(p.xy, layer)).xyz * 2.0 - 1.0;
	tx.xy *= bump;
	ty.xy *= bump;
	tz.xy *= bump;
	tx = vec3(tx.xy + n.zy, abs(tx.z) * n.x);
	ty = vec3(ty.xy + n.xz, abs(ty.z) * n.y);
	tz = vec3(tz.xy + n.xy, abs(tz.z) * n.z);
	nrm = normalize(tx.zyx * w.x + ty.xzy * w.y + tz.xyz * w.z);
	return alb;
}

// Fake global illumination: warm light bounced off the sunlit ground and
// nearby stone fills surfaces that face sideways or down (strongest low on
// walls, gone at night), plus a faint cool sky bounce on upward faces, so
// shade is coloured and soft instead of grey.
global uniform float night;
vec3 bounce_light(vec3 albedo, vec3 world_n, float height_above_ground) {
	float day = 1.0 - night;
	float side_down = clamp(0.6 - world_n.y * 0.7, 0.0, 1.0);
	float near_ground = mix(1.0, 0.55, smoothstep(0.0, 4.0, height_above_ground));
	vec3 ground = vec3(0.30, 0.24, 0.13) * side_down * near_ground;
	vec3 sky = vec3(0.05, 0.07, 0.1) * clamp(world_n.y, 0.0, 1.0);
	return albedo * (ground + sky) * day;
}
