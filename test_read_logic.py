from pathlib import Path
import plistlib
from logicx.projectdata import ProjectData

bundle = Path(r'C:\dev\daw2logic\Dawprojects\Find a way JP.logicx')
print(f'Loading: {bundle}\n')

# 1. Read metadata
meta = plistlib.loads((bundle / 'Alternatives/000/MetaData.plist').read_bytes())
audio_files = meta.get('AudioFiles', [])
print(f'Project Sample Rate: {meta.get("SampleRate")} Hz')
print(f'Total Audio Assets: {len(audio_files)}')

# 2. Read timeline placements
pd = ProjectData.parse((bundle / 'Alternatives/000/ProjectData').read_bytes())
placements = pd.audio_placements()
print(f'Total Timeline Regions Placed: {len(placements)}')

# 3. Print first 8 placed clips
print('\nSample Timeline Clips:')
for p in placements[:8]:
    track_num = p['track']
    start_tick = p['pos'] - 34560
    reg_idx = p['region_index']
    audio_name = audio_files[reg_idx] if reg_idx < len(audio_files) else 'Unknown'
    flag = hex(p['sel'])
    print(f'  Track {track_num:<2} | Tick: {start_tick:<6} | Flags: {flag} | Audio: {audio_name}')
