from pathlib import Path
from logicx.projectdata import ProjectData
from daw2logic.convert import logic_aud_ordinal
from daw2logic.track_order import audio_channels

# 1. Check ordinal formula
print('logic_aud_ordinal(1..10):', [logic_aud_ordinal(i) for i in range(1, 11)])

# 2. Check which track numbers Logic actually used for placements
bundle = Path(r'C:\dev\daw2logic\Dawprojects\Find a way JP.logicx')
pd = ProjectData.parse((bundle / 'Alternatives/000/ProjectData').read_bytes())
placements = pd.audio_placements()
placed_tracks = sorted(list(set(p['track'] for p in placements)))
print('Placed track numbers in Logic:', placed_tracks)

# 3. Check audio_channels mapping keys
aud_map = audio_channels(pd)
print('audio_channels keys:', sorted(list(aud_map.keys())))

# 4. Check how lFuA filename is read in projectdata.py
import inspect
from logicx.projectdata import ProjectData
lines = inspect.getsource(ProjectData._set_lfua_filename).split('\n')
for l in lines[:10]:
    print(' ', l)
