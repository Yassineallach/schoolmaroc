import {loadFont} from '@remotion/fonts';
import {Audio} from '@remotion/media';
import {linearTiming, TransitionSeries} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';
import {iris} from '@remotion/transitions/iris';
import {slide} from '@remotion/transitions/slide';
import {wipe} from '@remotion/transitions/wipe';
import React from 'react';
import {
	AbsoluteFill,
	Easing,
	Img,
	interpolate,
	spring,
	staticFile,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';
import data from '../public/a1/data.json';

// Act 1 of « Les très grands nombres », rebuilt in Remotion from the same assets, cues and
// soundtrack as the approved act (exported by the Python engine into public/a1).

const FONTS = [
	['Playfair', 'Playfair700.ttf', '700'],
	['PTSerif', 'PTSerif.ttf', '400'],
	['Inter', 'Inter600.ttf', '600'],
	['Inter', 'Inter400.ttf', '400'],
	['Archivo', 'ArchivoBlack.ttf', '400'],
	['SpecialElite', 'SpecialElite.ttf', '400'],
] as const;
for (const [family, file, weight] of FONTS) {
	loadFont({family, url: staticFile(`a1/${file}`), weight});
}

const C = data.cues;
const P = data.pal;
const FPS = 30;
export const ACT1_FRAMES = Math.round(C.end * FPS);
const T = 12; // transition overlap, frames

const f = (s: number) => Math.round(s * FPS);
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const ease = Easing.bezier(0.16, 1, 0.3, 1);

// ---------------------------------------------------------------- building blocks
const Ground: React.FC<{env: string}> = ({env}) => (
	<Img src={staticFile(`a1/bg_${env}.jpg`)} style={{position: 'absolute', inset: 0, width: 1920, height: 1080}} />
);

/** frames since `at` seconds of act time, inside a scene that starts at `from` seconds */
const useSince = (from: number) => {
	const frame = useCurrentFrame();
	return (at: number) => frame - f(at - from);
};

const Spring: React.FC<{
	from: number;
	at: number;
	children: React.ReactNode;
	x: number;
	y: number;
	rot?: number;
	dropFrom?: number;
	shadow?: boolean;
}> = ({from, at, children, x, y, rot = 0, dropFrom = -140, shadow = true}) => {
	const since = useSince(from)(at);
	const {fps} = useVideoConfig();
	const p = spring({frame: since, fps, config: {damping: 14, stiffness: 120, mass: 0.9}});
	if (since < 0) return null;
	return (
		<div
			style={{
				position: 'absolute',
				left: x,
				top: y,
				translate: `-50% calc(-50% + ${(1 - p) * dropFrom}px)`,
				rotate: `${rot + (1 - p) * 8}deg`,
				scale: String(1.04 - 0.04 * p),
				opacity: Math.min(1, since / 4),
				filter: shadow ? `drop-shadow(0 ${10 + 14 * (1 - p)}px ${14 + 18 * (1 - p)}px rgba(0,0,0,${0.24 - 0.08 * (1 - p)}))` : undefined,
			}}
		>
			{children}
		</div>
	);
};

const Caption: React.FC<{text: string; corner?: 'bl' | 'br'; from: number; at: number; dark?: boolean}> = ({text, corner = 'br', from, at, dark}) => {
	const since = useSince(from)(at);
	return (
		<div
			style={{
				position: 'absolute',
				bottom: 36,
				[corner === 'br' ? 'right' : 'left']: 36,
				fontFamily: 'PTSerif',
				fontSize: 24,
				color: dark ? P.light : P.ink,
				opacity: interpolate(since, [0, 18], [0, 0.9], clamp),
			}}
		>
			{text}
		</div>
	);
};

/** words rising one by one, each from its own slot, on their cue */
const Words: React.FC<{words: [string, number][]; from: number; size: number; color: string; family?: string; style?: React.CSSProperties}> = ({
	words,
	from,
	size,
	color,
	family = 'Playfair',
	style,
}) => {
	const since = useSince(from);
	const {fps} = useVideoConfig();
	return (
		<div style={{display: 'flex', gap: size * 0.28, justifyContent: 'center', ...style}}>
			{words.map(([w, at], i) => {
				const p = spring({frame: since(at), fps, config: {damping: 200}});
				return (
					<span key={i} style={{display: 'inline-block', overflow: 'hidden', lineHeight: 1.15, paddingBottom: size * 0.08}}>
						<span
							style={{
								display: 'inline-block',
								fontFamily: family,
								fontSize: size,
								color,
								translate: `0 ${(1 - p) * 110}%`,
								opacity: since(at) < 0 ? 0 : 1,
							}}
						>
							{w}
						</span>
					</span>
				);
			})}
		</div>
	);
};

const NameCard: React.FC<{name: string; role: string; from: number; at: number; x: number; y: number}> = ({name, role, from, at, x, y}) => {
	const s = useSince(from)(at);
	const {fps} = useVideoConfig();
	const p = spring({frame: s, fps, config: {damping: 200}});
	const bar = interpolate(s, [10, 26], [0, 140], {...clamp, easing: ease});
	if (s < 0) return null;
	return (
		<div style={{position: 'absolute', left: x, top: y}}>
			<div style={{fontFamily: 'Inter', fontWeight: 600, fontSize: 24, letterSpacing: 6, color: P.ink, opacity: p}}>{role}</div>
			<div style={{overflow: 'hidden'}}>
				<div style={{fontFamily: 'Playfair', fontSize: 92, color: P.ink, translate: `0 ${(1 - p) * 100}%`}}>{name}</div>
			</div>
			<div style={{width: bar, height: 8, background: P.accent, marginTop: 6}} />
		</div>
	);
};

const Watermark: React.FC = () => (
	<Img src={staticFile('a1/logo.svg')} style={{position: 'absolute', top: 46, right: 52, width: 112, opacity: 0.62, background: '#2B2A2A', padding: '6px 9px', borderRadius: 4}} />
);

// board geometry (same image and centre maths as the Python engine)
const BOARD = 760;
const sq = (cx: number, cy: number, k: number, size = BOARD) => {
	const s = size / 8;
	const i = (k - 1) % 8;
	const j = Math.floor((k - 1) / 8);
	return [cx - size / 2 + (i + 0.5) * s, cy - size / 2 + (j + 0.5) * s] as const;
};

const Grains: React.FC<{from: number; at: number; x: number; y: number; n: number; spread: number; seed: number; size?: number}> = ({
	from,
	at,
	x,
	y,
	n,
	spread,
	seed,
	size = 1,
}) => {
	const since = useSince(from)(at);
	const items = [];
	for (let i = 0; i < n; i++) {
		const r1 = Math.sin(seed * 91 + i * 12.9898) * 43758.5453;
		const r2 = Math.sin(seed * 37 + i * 78.233) * 12345.6789;
		const dx = ((r1 - Math.floor(r1)) * 2 - 1) * spread;
		const dy = ((r2 - Math.floor(r2)) * 2 - 1) * spread;
		const delay = Math.round(8 * Math.pow(i / Math.max(1, n - 1), 0.7));
		const k = interpolate(since - delay, [0, 7], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
		if (since - delay < 0) continue;
		items.push(
			<Img
				key={i}
				src={staticFile(`a1/grain${(i + seed) % 8}.png`)}
				style={{
					position: 'absolute',
					left: x + dx,
					top: y + dy - 26 * (1 - k),
					width: 62 * size,
					translate: '-50% -50%',
					opacity: k,
					filter: 'drop-shadow(0 3px 3px rgba(0,0,0,.25))',
				}}
			/>,
		);
	}
	return <>{items}</>;
};

// ---------------------------------------------------------------- the scenes
const S = data.shots;
const G01W = data.geo.g01[0];
const G01H = data.geo.g01[1];

const Opening: React.FC = () => {
	const frame = useCurrentFrame();
	const dur = f(S[1] - S[0]) + T;
	const k = interpolate(frame, [0, dur], [0, 1], {...clamp, easing: Easing.inOut(Easing.sin)});
	const z = 1 + 0.16 * k;
	const [cx, cy] = data.geo.chess;
	return (
		<AbsoluteFill>
			<Ground env="cream" />
			<AbsoluteFill style={{scale: String(z), transformOrigin: `${960 + (cx - 960) * k}px ${540 + (cy - 120 - 540) * k}px`}}>
				<Img src={staticFile('a1/g01.png')} style={{position: 'absolute', left: 960 - G01W / 2, top: 540 - G01H / 2, width: G01W}} />
			</AbsoluteFill>
			<Caption text="Illustration" corner="bl" from={S[0]} at={1.2} />
		</AbsoluteFill>
	);
};

const Kicker: React.FC<{from: number}> = ({from}) => {
	const s = useSince(from)(from + 0.6);
	const txt = 'UN GRAIN SUR LA PREMIÈRE CASE';
	const n = Math.max(0, Math.min(txt.length, Math.floor((s - 8) / 1)));
	const out = interpolate(s, [170, 190], [1, 0], clamp);
	if (s < 0) return null;
	return (
		<div style={{position: 'absolute', left: 64, top: 925, display: 'flex', gap: 22, alignItems: 'center', opacity: out}}>
			<span style={{fontFamily: 'Archivo', fontSize: 34, color: P.accent}}>01</span>
			<span style={{fontFamily: 'SpecialElite', fontSize: 30, color: P.ink}}>{txt.slice(0, n)}</span>
		</div>
	);
};

const Vizir: React.FC = () => (
	<AbsoluteFill>
		<Ground env="theme" />
		<Img src={staticFile('a1/board.png')} style={{position: 'absolute', left: 1330 - 280, top: 560 - 280, width: 560, filter: 'drop-shadow(0 10px 16px rgba(0,0,0,.22))'}} />
		<Spring from={S[1]} at={C.demande - 0.1} x={600} y={540} rot={-2}>
			<Img src={staticFile('a1/g03.png')} style={{width: 560}} />
		</Spring>
		<Kicker from={S[1]} />
		<Caption text="Illustration" corner="bl" from={S[1]} at={C.demande + 0.8} />
	</AbsoluteFill>
);

const Doubling: React.FC = () => {
	const since = useSince(S[2]);
	const push = interpolate(since(C.doublant), [0, 48], [1, 1.1], {...clamp, easing: Easing.inOut(Easing.sin)});
	const marks: [number, number, number][] = [
		[C.un_grain, 1, 1],
		[C.deux, 2, 2],
		[C.quatre, 3, 4],
	];
	return (
		<AbsoluteFill>
			<Ground env="paper" />
			<AbsoluteFill style={{scale: String(push), transformOrigin: `${960 - 220}px ${560 - 290}px`}}>
				<Img src={staticFile('a1/board.png')} style={{position: 'absolute', left: 960 - 414, top: 560 - 414, width: 828, filter: 'drop-shadow(0 12px 18px rgba(0,0,0,.22))'}} />
				{marks.map(([at, k, n]) => {
					const [x, y] = sq(960, 560, k);
					const p = spring({frame: since(at + 0.2), fps: FPS, config: {damping: 200}});
					return (
						<React.Fragment key={k}>
							<Grains from={S[2]} at={at} x={x} y={y} n={n} spread={20} seed={k} />
							<div style={{position: 'absolute', left: x, top: y + 58, translate: '-50% 0', fontFamily: 'Archivo', fontSize: 34, color: P.accent, opacity: since(at + 0.2) < 0 ? 0 : p}}>
								{n}
							</div>
						</React.Fragment>
					);
				})}
				{[4, 5, 6, 7, 8].map((k) => {
					const [x, y] = sq(960, 560, k);
					return <Grains key={k} from={S[2]} at={C.doublant + 0.32 * (k - 4)} x={x} y={y} n={2 ** (k - 1)} spread={30} seed={k} size={0.7} />;
				})}
			</AbsoluteFill>
		</AbsoluteFill>
	);
};

const King: React.FC = () => {
	const since = useSince(S[3]);
	const k = interpolate(since(C.intendants), [0, 48], [0, 1], {...clamp, easing: Easing.inOut(Easing.sin)});
	const [kx, ky] = data.geo.king;
	const z = 2.1 - 1.0 * k;
	const fx = kx + (960 - kx) * k;
	const fy = ky + (540 - ky) * k;
	return (
		<AbsoluteFill>
			<Ground env="cream" />
			<AbsoluteFill style={{scale: String(z), translate: `${(960 - fx) * z}px ${(540 - fy) * z}px`}}>
				<Img src={staticFile('a1/g01.png')} style={{position: 'absolute', left: 960 - G01W / 2, top: 540 - G01H / 2, width: G01W}} />
			</AbsoluteFill>
		</AbsoluteFill>
	);
};

const EmptySack: React.FC = () => {
	const since = useSince(S[4]);
	const enter = spring({frame: since(S[4] - 0.36), fps: FPS, config: {damping: 18, stiffness: 90}});
	const [x, y] = sq(1340, 540, 20, 560 * (760 / 828));
	const ring = interpolate(since(C.vingtieme), [0, 14], [0, 1], {...clamp, easing: ease});
	const circ = 2 * Math.PI * 48;
	return (
		<AbsoluteFill>
			<Ground env="theme" />
			<Img src={staticFile('a1/g02.png')} style={{position: 'absolute', left: 560 - 500, top: 540 - 281, width: 1000, translate: `${(1 - enter) * -900}px 0`, rotate: `${-3 + (1 - enter) * -6}deg`}} />
			<Img src={staticFile('a1/board.png')} style={{position: 'absolute', left: 1340 - 280, top: 540 - 280, width: 560, filter: 'drop-shadow(0 10px 16px rgba(0,0,0,.22))'}} />
			<svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
				<circle cx={x} cy={y} r={48} fill="none" stroke={P.accent} strokeWidth={7} strokeLinecap="round" strokeDasharray={circ} strokeDashoffset={circ * (1 - ring * 1.1)} transform={`rotate(-110 ${x} ${y})`} />
			</svg>
			<Caption text="Illustration" corner="bl" from={S[4]} at={S[4] + 0.6} />
		</AbsoluteFill>
	);
};

const Eighteen: React.FC = () => {
	const since = useSince(S[5]);
	const d = since(C.dix);
	const roll = interpolate(d, [0, 28], [0, 18], {...clamp, easing: ease});
	return (
		<AbsoluteFill>
			<Ground env="accent" />
			<Img src={staticFile('a1/board.png')} style={{position: 'absolute', left: 470 - 280, top: 540 - 280, width: 560, rotate: '4deg', filter: 'drop-shadow(0 12px 20px rgba(0,0,0,.3))'}} />
			<div style={{position: 'absolute', left: 1300, top: 300, translate: '-50% 0', fontFamily: 'Archivo', fontSize: 240, color: P.light, opacity: d < 0 ? 0 : 1, lineHeight: 1}}>
				{Math.round(roll)}
			</div>
			<Words
				from={S[5]}
				size={76}
				color={P.light}
				style={{position: 'absolute', left: 860, width: 880, top: 600, flexWrap: 'wrap'}}
				words={[
					['milliards', C.milliards],
					['de', C.milliards + 0.25],
					['milliards', C.milliards + 0.45],
					['de', C.milliards + 0.75],
					['grains', C.milliards + 0.95],
				]}
			/>
		</AbsoluteFill>
	);
};

const Harvest: React.FC = () => {
	const since = useSince(S[6]);
	const many = since(C.mille);
	const cols = 56;
	const cell = 21;
	const ox = (1920 - cols * cell) / 2;
	const oy = 250;
	const u = interpolate(many, [-6, 18], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
	const size = 200 + (cell - 4 - 200) * u;
	const cx = 960 + (ox + cell / 2 - 960) * u;
	const cy = 520 + (oy + cell / 2 - 520) * u;
	const rects = [];
	for (let i = 1; i < 1400; i++) {
		const at = Math.round(42 * Math.pow(i / 1400, 0.8));
		const k = interpolate(many - at, [0, 7], [0, 1], clamp);
		if (k <= 0) continue;
		rects.push(<rect key={i} x={ox + (i % cols) * cell + 2} y={oy + Math.floor(i / cols) * cell + 2} width={cell - 4} height={cell - 4} fill={P.accent} opacity={k} />);
	}
	const xLabel = spring({frame: many - 18, fps: FPS, config: {damping: 12}});
	return (
		<AbsoluteFill>
			<Ground env="grid" />
			<svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
				{rects}
				<rect x={cx - size / 2} y={cy - size / 2} width={size} height={size} fill="#BE9646" />
			</svg>
			<div style={{position: 'absolute', top: 660, width: 1920, textAlign: 'center', fontFamily: 'Inter', fontWeight: 600, fontSize: 30, letterSpacing: 6, color: P.ink, opacity: interpolate(many, [-14, -4], [1, 0], clamp)}}>
				1 AN DE RÉCOLTE MONDIALE
			</div>
			{many >= 18 && (
				<div style={{position: 'absolute', top: 820, width: 1920, textAlign: 'center', fontFamily: 'Archivo', fontSize: 120, color: P.accent, scale: String(xLabel)}}>× 1 400</div>
			)}
		</AbsoluteFill>
	);
};

const Khallikan: React.FC = () => {
	const since = useSince(S[7]);
	const enter = spring({frame: since(S[7] - 0.36), fps: FPS, config: {damping: 18, stiffness: 90}});
	return (
		<AbsoluteFill>
			<Ground env="archive" />
			<Img src={staticFile('a1/board.png')} style={{position: 'absolute', left: 560 - 280, top: 560 - 280, width: 560, translate: `${(1 - enter) * -960}px 0`, rotate: '-3deg', filter: 'drop-shadow(0 12px 18px rgba(0,0,0,.25))'}} />
			<NameCard name="Ibn Khallikan" role="HISTORIEN · 1256" from={S[7]} at={C['1256']} x={1020} y={430} />
		</AbsoluteFill>
	);
};

const Title: React.FC = () => (
	<AbsoluteFill>
		<Ground env="charcoal" />
		<Words
			from={S[8]}
			size={118}
			color={P.light}
			style={{position: 'absolute', top: 470, width: 1920}}
			words={[
				['Les', S[8] + 0.2],
				['très', C.tres],
				['grands', C.grands],
				['nombres', C.nombres],
			]}
		/>
	</AbsoluteFill>
);

const Gamow: React.FC = () => {
	const since = useSince(S[9]);
	const book = spring({frame: since(C.raconte), fps: FPS, config: {damping: 14, stiffness: 110}});
	const tag = spring({frame: since(C.shirham), fps: FPS, config: {damping: 200}});
	return (
		<AbsoluteFill>
			<Ground env="theme" />
			<Spring from={S[9]} at={S[9] - 0.3} x={470} y={470} rot={-3}>
				<Img src={staticFile('a1/gamow.png')} style={{width: 330}} />
			</Spring>
			<NameCard name="George Gamow" role="PHYSICIEN · 1947" from={S[9]} at={C.physicien} x={820} y={300} />
			{since(C.raconte) >= 0 && (
				<div style={{position: 'absolute', left: 1080, top: 650, translate: `-50% calc(-50% + ${(1 - book) * -120}px)`, rotate: `${2.5 + (1 - book) * 6}deg`, width: 500, padding: '42px 0', background: P.light, boxShadow: '0 14px 26px rgba(0,0,0,.22)', textAlign: 'center', fontFamily: 'PTSerif', fontSize: 46, color: P.ink, lineHeight: 1.25}}>
					« Un, deux, trois…
					<br />
					l’infini »
				</div>
			)}
			{since(C.shirham) >= 0 && (
				<div style={{position: 'absolute', left: 1520, top: 820, translate: '-50% -50%', padding: '10px 26px', background: P.accent, color: P.light, fontFamily: 'Archivo', fontSize: 54, clipPath: `inset(0 ${(1 - tag) * 100}% 0 0)`}}>Shirham</div>
			)}
			<Caption text="George Gamow" from={S[9]} at={S[9] + 1} />
		</AbsoluteFill>
	);
};

// ---------------------------------------------------------------- the act
const SCENES: [string, React.FC][] = [
	['Opening', Opening],
	['Vizir', Vizir],
	['Doubling', Doubling],
	['King', King],
	['EmptySack', EmptySack],
	['Eighteen', Eighteen],
	['Harvest', Harvest],
	['Khallikan', Khallikan],
	['Title', Title],
	['Gamow', Gamow],
];
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const PRESENTATIONS: any[] = [
	slide({direction: 'from-bottom'}),
	wipe({direction: 'from-left'}),
	iris({width: 1920, height: 1080}),
	wipe({direction: 'from-right'}),
	slide({direction: 'from-bottom'}),
	wipe({direction: 'from-left'}),
	slide({direction: 'from-right'}),
	fade(),
	slide({direction: 'from-bottom'}),
];

export const Act1: React.FC = () => {
	const bounds = [...S, C.end];
	return (
		<AbsoluteFill style={{background: P.light}}>
			<TransitionSeries>
				{SCENES.map(([name, Scene], i) => {
					const len = f(bounds[i + 1]) - f(bounds[i]) + (i < SCENES.length - 1 ? T : 0);
					return (
						<React.Fragment key={name}>
							<TransitionSeries.Sequence name={name} durationInFrames={len}>
								<Scene />
							</TransitionSeries.Sequence>
							{i < SCENES.length - 1 && <TransitionSeries.Transition presentation={PRESENTATIONS[i]} timing={linearTiming({durationInFrames: T})} />}
						</React.Fragment>
					);
				})}
			</TransitionSeries>
			<Watermark />
			<Audio src={staticFile('a1/act1.m4a')} />
		</AbsoluteFill>
	);
};
