import zipfile, plistlib, struct
from pathlib import Path
import xml.etree.ElementTree as ET
from logicx.projectdata import ProjectData

print('=' * 65)
print(' 1. ORIGINAL CUBASE FILE (Find a way JP.dawproject)')
print('=' * 65)
with zipfile.ZipFile(r'C:\dev\daw2logic\Dawprojects\Find a way JP.dawproject') as z:
    orig = ET.fromstring(z.read('project.xml'))

melody_id = None
for t in orig.findall('.//Structure/Track'):
    if t.get('name') == 'Melody (R)':
        melody_id = t.get('id')
        break

for lane in orig.findall('.//Arrangement//Lanes'):
    if lane.get('track') == melody_id:
        for c in lane.findall('.//Clip'):
            name = c.get('name')
            if name:
                time_val = float(c.get('time', 0))
                bar_val = (time_val / 4.0) + 1.0
                print('  Orig Clip:', name, '| Beat:', time_val, '| Bar:', bar_val)

print('\n' + '=' * 65)
print(' 2. LOGIC PROJECT (ProjectData lFuA) - Track 25')
print('=' * 65)
bundle = Path(r'C:\dev\daw2logic\Dawprojects\Find a way JP.logicx')
pd = ProjectData.parse((bundle / 'Alternatives/000/ProjectData').read_bytes())
meta = plistlib.loads((bundle / 'Alternatives/000/MetaData.plist').read_bytes())
sr = meta.get('SampleRate', 44100)
tempo = meta.get('BeatsPerMinute', 120.0)
slots_by_idx = pd._region_records_by_index()

placements = [p for p in pd.audio_placements() if p['track'] == 25]
for p in placements:
    tick = p['pos'] - 34560
    beat = tick / 960.0
    bar = (beat / 4.0) + 1.0
    reg_idx = p['region_index']
    
    # Read real filename from lFuA
    fn = 'Unknown'
    sample_len = 0
    slots = slots_by_idx.get(reg_idx)
    if slots:
        if 'lFuA' in slots:
            r = pd.records[slots['lFuA']]
            nlen = struct.unpack_from('<H', r.raw, 0x24 + 0x08)[0]
            fn = r.raw[0x24 + 0x0a : 0x24 + 0x0a + nlen * 2].decode('utf-16le', 'ignore')
        if 'gRuA' in slots:
            gr = pd.records[slots['gRuA']]
            sample_len = struct.unpack_from('<I', gr.raw, 0x24 + pd.GRUA_SAMPLELEN_OFF)[0]
    
    dur_sec = sample_len / sr
    dur_beats = dur_sec * (tempo / 60.0)
    print('  Logic Clip:', fn, '| Beat:', beat, '| Bar:', bar, '| Dur(beats):', round(dur_beats, 2))
