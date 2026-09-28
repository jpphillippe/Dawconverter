import zipfile, plistlib
from pathlib import Path
import xml.etree.ElementTree as ET
from logicx.projectdata import ProjectData

# 1. Original DAWproject clips on first track
with zipfile.ZipFile(r'C:\dev\daw2logic\Dawprojects\Find a way JP.dawproject') as z:
    orig = ET.fromstring(z.read('project.xml'))

orig_lane = orig.find('.//Arrangement//Lanes[@track]')
print(f'Original Track ID: {orig_lane.get(\"track\")}')
for c in orig_lane.findall('.//Clip')[:4]:
    print(f'  Orig Clip: time={c.get(\"time\")} | duration={c.get(\"duration\")} | name={c.get(\"name\")}')

# 2. Logic placements on Track 1
bundle = Path(r'C:\dev\daw2logic\Dawprojects\Find a way JP.logicx')
pd = ProjectData.parse((bundle / 'Alternatives/000/ProjectData').read_bytes())
meta = plistlib.loads((bundle / 'Alternatives/000/MetaData.plist').read_bytes())
sr = meta.get('SampleRate', 44100)
tempo = meta.get('BeatsPerMinute', 120.0)

print(f'\nLogic Track 1 Placements (Tempo: {tempo}, SR: {sr}):')
placements = [p for p in pd.audio_placements() if p['track'] == 1]
slots_by_idx = pd._region_records_by_index()

for p in placements[:4]:
    pos_raw = p['pos']
    reg_idx = p['region_index']
    # Read sample_len from gRuA record
    sample_len = 0
    slots = slots_by_idx.get(reg_idx)
    if slots and 'gRuA' in slots:
        r = pd.records[slots['gRuA']]
        import struct
        sample_len = struct.unpack_from('<I', r.raw, 0x24 + pd.GRUA_SAMPLELEN_OFF)[0]
    
    dur_sec = sample_len / sr
    dur_beats = dur_sec * (tempo / 60.0)
    print(f'  Logic Placement: pos_raw={pos_raw} | sample_len={sample_len} ({dur_sec:.3f}s / {dur_beats:.2f} beats)')
