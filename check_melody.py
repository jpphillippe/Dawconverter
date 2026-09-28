import zipfile, plistlib
from pathlib import Path
import xml.etree.ElementTree as ET
from logicx.projectdata import ProjectData

print('=' * 60)
print(' 1. ORIGINAL DAWPROJECT - Melody (R)')
print('=' * 60)
with zipfile.ZipFile(r'C:\dev\daw2logic\Dawprojects\Find a way JP.dawproject') as z:
    orig = ET.fromstring(z.read('project.xml'))

# Find Melody track ID
melody_id = None
for t in orig.findall('.//Structure/Track'):
    if t.get('name') == 'Melody (R)':
        melody_id = t.get('id')
        print('Found Track:', t.get('name'), 'ID:', melody_id)
        break

if melody_id:
    for lane in orig.findall('.//Arrangement//Lanes'):
        if lane.get('track') == melody_id:
            for c in lane.findall('.//Clip'):
                audio_file = c.find('.//File')
                fn = audio_file.get('path') if audio_file is not None else 'no file'
                print('  Orig Clip:', c.get('name'), '| time:', c.get('time'), '| file:', fn)

print('\n' + '=' * 60)
print(' 2. LOGIC PROJECT (ProjectData) - Melody (R)')
print('=' * 60)
bundle = Path(r'C:\dev\daw2logic\Dawprojects\Find a way JP.logicx')
pd = ProjectData.parse((bundle / 'Alternatives/000/ProjectData').read_bytes())
meta = plistlib.loads((bundle / 'Alternatives/000/MetaData.plist').read_bytes())
audio_files = meta.get('AudioFiles', [])
tempo = float(meta.get('BeatsPerMinute', 120.0))

# Track 25 was Melody (R)
placements = [p for p in pd.audio_placements() if p['track'] == 25]
print('Total placements on Track 25 in Logic:', len(placements))
for p in placements[:8]:
    tick = p['pos'] - 34560
    beat = tick / 960.0
    bar = (beat / 4.0) + 1.0
    reg_idx = p['region_index']
    audio_name = audio_files[reg_idx] if reg_idx < len(audio_files) else 'Unknown'
    print('  Logic Placed at tick:', tick, f'| beat: {beat:.1f}', f'| Bar: {bar:.1f}', '| audio:', audio_name)
