import zipfile, struct
from pathlib import Path
import xml.etree.ElementTree as ET
from logicx.projectdata import ProjectData

print('=' * 65)
print(' 1. ORIGINAL CUBASE FILE - Stabs Track')
print('=' * 65)
with zipfile.ZipFile(r'C:\dev\daw2logic\Dawprojects\Find a way JP.dawproject') as z:
    orig = ET.fromstring(z.read('project.xml'))

stabs_id = next((t.get('id') for t in orig.findall('.//Structure/Track') if t.get('name') == 'Stabs'), None)
print('Stabs Track ID in Orig:', stabs_id)

for lane in orig.findall('.//Arrangement//Lanes'):
    if lane.get('track') == stabs_id:
        for c in lane.findall('.//Clip'):
            # Print outer and inner clip attributes
            inner = c.find('.//Clips/Clip')
            inner_attrs = inner.attrib if inner is not None else {}
            print('  Orig Clip:', c.get('name'))
            print('    Outer attrs:', c.attrib)
            print('    Inner attrs:', inner_attrs)

print('\n' + '=' * 65)
print(' 2. LOGIC PROJECT (gRuA records) - Stabs Track Placements')
print('=' * 65)
bundle = Path(r'C:\dev\daw2logic\Dawprojects\Find a way JP.logicx')
pd = ProjectData.parse((bundle / 'Alternatives/000/ProjectData').read_bytes())
slots_by_idx = pd._region_records_by_index()

# Track 20 was Stabs
stabs_placements = [p for p in pd.audio_placements() if p['track'] == 20]
print(f'Total placements on Track 20 in Logic: {len(stabs_placements)}')

for i, p in enumerate(stabs_placements):
    tick = p['pos'] - 34560
    bar = (tick / 960.0 / 4.0) + 1.0
    reg_idx = p['region_index']
    slots = slots_by_idx.get(reg_idx)
    
    fn = 'Unknown'
    grua_hex = ''
    if slots:
        if 'lFuA' in slots:
            r = pd.records[slots['lFuA']]
            nlen = struct.unpack_from('<H', r.raw, 0x24 + 0x08)[0]
            fn = r.raw[0x24 + 0x0a : 0x24 + 0x0a + nlen * 2].decode('utf-16le', 'ignore')
        if 'gRuA' in slots:
            gr = pd.records[slots['gRuA']]
            # Inspect first 48 bytes of gRuA payload
            grua_hex = gr.raw[0x24:0x24 + 32].hex(' ')

    print(f'  Logic Clip #{i+1}: File={fn} | Bar={bar}')
    print(f'    gRuA payload header: {grua_hex}')
