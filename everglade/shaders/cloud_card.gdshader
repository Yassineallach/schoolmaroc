// Painted cumulus billboards: a 2x2 atlas of hand-painted cloud cards, turned
// to face the camera around the vertical axis and tinted by the time of day.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform sampler2D cloud_tex : source_color, filter_linear_mipmap, repeat_disable;
uniform vec4 lit_color : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform vec4 shade_color : source_color = vec4(0.74, 0.80, 0.96, 1.0);
uniform vec3 sun_dir = vec3(0.3, 0.8, 0.2);

varying vec2 v_cell;
varying float v_side;

void vertex() {
	// cylindrical billboard
	vec3 origin = MODEL_MATRIX[3].xyz;
	vec3 to_cam = CAMERA_POSITION_WORLD - origin;
	to_cam.y = 0.0;
	vec3 fwd = normalize(to_cam);
	vec3 right = normalize(cross(vec3(0.0, 1.0, 0.0), fwd));
	float sx = length(MODEL_MATRIX[0].xyz);
	float sy = length(MODEL_MATRIX[1].xyz);
	vec3 world = origin + right * VERTEX.x * sx + vec3(0.0, 1.0, 0.0) * VERTEX.y * sy;
	POSITION = PROJECTION_MATRIX * VIEW_MATRIX * vec4(world, 1.0);
	v_cell = INSTANCE_CUSTOM.xy;
	// is the sun on the camera's side of the cloud? (front lit vs back lit)
	v_side = dot(-fwd, normalize(vec3(sun_dir.x, 0.0, sun_dir.z)));
}

void fragment() {
	vec2 uv = vec2(UV.x, mix(0.12, 0.74, UV.y));
	vec4 tex = texture(cloud_tex, (v_cell + uv) * 0.5);
	float lum = dot(tex.rgb, vec3(0.3, 0.59, 0.11));
	// painted bands: soft bright tops, cool bellies
	float lit = smoothstep(0.72, 0.9, lum);
	lit = mix(lit, lit * 0.85 + 0.15, step(v_side, 0.0));
	vec3 col = mix(shade_color.rgb, lit_color.rgb, lit);
	ALBEDO = col;
	ALPHA = tex.a;
}
