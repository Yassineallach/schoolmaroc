import {Composition} from 'remotion';
import {Act1, ACT1_FRAMES} from './Act1';

export const RemotionRoot: React.FC = () => {
	return (
		<>
			<Composition id="Act1" component={Act1} durationInFrames={ACT1_FRAMES} fps={30} width={1920} height={1080} />
		</>
	);
};
