import zipfile, plistlib, struct
from pathlib import Path
import xml.etree.ElementTree as ET
from logicx.projectdata import ProjectData, IVNE_IDX, _u32
from daw2logic.track_order import audio_channels

jp1_path = Path(r'C:\dev\daw2logic\Dawprojects\Find a way JP.dawproject')
jp2_path = Path(r'C:\dev\daw2logic\Dawprojects\Find a way JP2.dawproject')
logic_path = Path(r'C:\dev\daw2logic\Dawprojects\Find a way JP.logicx')

print('=' * 65)
print(' 3-WAY COMPARISON: JP1 vs JP2 vs LOGICX')
print('=' * 65)

def inspect_dawproject(path: Path, label: str):
    if not path.exists():
        print(f'[{label}] File NOT found: {path}')
        return None
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read('project.xml'))
        audio_files = [f for f in z.namelist() if f.lower().endswith(('.wav', '.flac', '.ogg'))]
    
    tracks = root.findall('.//Structure/Track')
    lanes = root.findall('.//Arrangement//Lanes[@track]')
    clips = root.findall('.//Clip')
    tempo = root.find('.//Transport/Tempo')
    tempo_val = tempo.get('value') if tempo is not None else 'Unknown'
    
    track_names = [t.get('name') for t in tracks]
    print(f'[{label}] Path: {path.name}')
    print(f'  Tempo: {tempo_val} | Audio Files in zip: {len(audio_files)}')
    print(f'  Total Tracks: {len(tracks)} | Track Lanes: {len(lanes)} | Total Clips: {len(clips)}')
    return {'root': root, 'tracks': tracks, 'track_names': track_names, 'audio_files': audio_files}

# 1. Inspect JP1 and JP2
jp1 = inspect_dawproject(jp1_path, 'JP1')
print()
jp2 = inspect_dawproject(jp2_path, 'JP2')

# 2. Inspect Logic
print(f'\n[LOGICX] Path: {logic_path.name}')
meta = plistlib.loads((logic_path / 'Alternatives/000/MetaData.plist').read_bytes())
pd = ProjectData.parse((logic_path / 'Alternatives/000/ProjectData').read_bytes())
aud_map = audio_channels(pd)
placements = pd.audio_placements()
print(f'  Sample Rate: {meta.get("SampleRate")} | Tempo: {meta.get("BeatsPerMinute")}')
print(f'  Total Audio Tracks in Logic: {len(aud_map)} | Placements: {len(placements)}')

# 3. Track List Differences between JP1 and JP2
if jp1 and jp2:
    print('\n' + '=' * 65)
    print(' TRACK COMPARISON (JP1 vs JP2)')
    print('=' * 65)
    t1 = jp1['track_names']
    t2 = jp2['track_names']
    if t1 == t2:
        print('  Track names and order are IDENTICAL between JP1 and JP2.')
    else:
        print(f'  Track counts differ: JP1 has {len(t1)} tracks, JP2 has {len(t2)} tracks.')
        added_in_jp2 = [x for x in t2 if x not in t1]
        removed_in_jp2 = [x for x in t1 if x not in t2]
        if added_in_jp2:
            print('  Added in JP2:', added_in_jp2)
        if removed_in_jp2:
            print('  Missing from JP2:', removed_in_jp2)

# 4. Compare "Melody (R)" clips between JP1, JP2, and Logic
print('\n' + '=' * 65)
print(' MELODY (R) CLIPS COMPARISON')
print('=' * 65)

def print_melody_clips(dp_data, label):
    if not dp_data: return
    root = dp_data['root']
    mel_id = next((t.get('id') for t in root.findall('.//Structure/Track') if t.get('name') == 'Melody (R)'), None)
    if not mel_id:
        print(f'  [{label}] Melody (R) track NOT found.')
        return
    clips = []
    for l in root.findall('.//Arrangement//Lanes'):
        if l.get('track') == mel_id:
            for c in l.findall('.//Clip'):
                name = c.get('name')
                if name:
                    time_b = float(c.get('time', 0))
                    bar = (time_b / 4.0) + 1.0
                    clips.append((name, time_b, bar))
    print(f'  [{label}] Total clips on Melody (R): {len(clips)}')
    for name, b, bar in clips[:6]:
        print(f'    Beat {b:<5} (Bar {bar:<5}): {name}')

print_melody_clips(jp1, 'JP1')
print_melody_clips(jp2, 'JP2')

# Logic Melody (R) - Track 25
slots_by_idx = pd._region_records_by_index()
mel_logic = [p for p in placements if p['track'] == 25]
print(f'  [LOGICX] Total placements on Track 25: {len(mel_logic)}')
for p in mel_logic[:6]:
    tick = p['pos'] - 34560
    b = tick / 960.0
    bar = (b / 4.0) + 1.0
    fn = 'Unknown'
    slots = slots_by_idx.get(p['region_index'])
    if slots and 'lFuA' in slots:
        r = pd.records[slots['lFuA']]
        nlen = struct.unpack_from('<H', r.raw, 0x24 + 0x08)[0]
        fn = r.raw[0x24 + 0x0a : 0x24 + 0x0a + nlen * 2].decode('utf-16le', 'ignore')
    print(f'    Beat {b:<5} (Bar {bar:<5}): {fn}')
