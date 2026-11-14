// Word cues for a Remotion scene, from the words.json written by SK/scripts/remotion_export.py.
// Same rules as the Python cue(): accents and punctuation folded, first occurrence unless nth,
// elisions split by Whisper (« l'Inde » -> "l" + "'Inde") cued by the second token.
//   import words from '../public/a1/words.json';
//   const cue = makeCue(words);
//   cue(1, 'Le vizir')          // act-local seconds of that phrase
//   Math.round(cue(1, 'demande') * fps)
type Word = {w: string; s: number; e: number};
type Words = {clips: Record<string, Word[]>; offset: Record<string, number>; end: number};

const norm = (s: string) =>
	s
		.toLowerCase()
		.replace(/’/g, "'")
		.normalize('NFKD')
		.replace(/[̀-ͯ]/g, '')
		.replace(/[^a-z0-9']/g, '');

export const makeCue = (data: Words) => {
	const cue = (clip: number, phrase: string, nth = 1, edge: 's' | 'e' = 's') => {
		const toks = phrase.split(/\s+/).map(norm).filter(Boolean);
		const ws = data.clips[String(clip)];
		const nw = ws.map((w) => norm(w.w));
		let hits = 0;
		for (let i = 0; i + toks.length <= nw.length; i++) {
			if (toks.every((t, j) => nw[i + j] === t)) {
				hits++;
				if (hits === nth) {
					const w = edge === 's' ? ws[i] : ws[i + toks.length - 1];
					return data.offset[String(clip)] + w[edge];
				}
			}
		}
		throw new Error(`clip ${clip}: "${phrase}" not found (${hits} hits)`);
	};
	return Object.assign(cue, {end: data.end});
};
