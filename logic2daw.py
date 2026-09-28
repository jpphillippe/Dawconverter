import sys, os, struct, plistlib, zipfile, wave
from pathlib import Path
import xml.etree.ElementTree as ET
from logicx.projectdata import ProjectData, IVNE_IDX, _u32
from daw2logic.track_order import audio_channels

def convert_logic_to_dawproject(logicx_dir: Path, output_file: Path):
    logicx_dir = Path(logicx_dir)
    output_file = Path(output_file)

    print(f'Reading Logic bundle: {logicx_dir.name}...')

    # 1. Read metadata
    meta_path = logicx_dir / 'Alternatives/000/MetaData.plist'
    meta = plistlib.loads(meta_path.read_bytes())
    tempo = float(meta.get('BeatsPerMinute', 120.0))
    sample_rate = int(meta.get('SampleRate', 44100))
    ts_num = int(meta.get('SongSignatureNumerator', 4))
    ts_den = int(meta.get('SongSignatureDenominator', 4))

    print(f'  Tempo: {tempo} BPM | Sample Rate: {sample_rate} Hz | Time Sig: {ts_num}/{ts_den}')

    # 2. Parse ProjectData binary
    pd_path = logicx_dir / 'Alternatives/000/ProjectData'
    pd = ProjectData.parse(pd_path.read_bytes())
    slots_by_idx = pd._region_records_by_index()

    # 3. Resolve Track Names
    aud_map = audio_channels(pd)
    track_names = {}
    for track_num, chan_id in aud_map.items():
        iv = next((r for r in pd.records if r.tag == b'ivnE' and _u32(r.raw, IVNE_IDX) == chan_id), None)
        if iv and len(iv.raw) > 0xc4:
            n = struct.unpack_from('<H', iv.raw, 0xc2)[0]
            name = iv.raw[0xc4:0xc4 + n].decode('latin-1', 'replace').strip()
            track_names[track_num] = name if name else f'Audio {track_num}'
        else:
            track_names[track_num] = f'Audio {track_num}'

    print(f'  Found {len(track_names)} audio tracks.')

    # 4. Group timeline placements by track
    placements = pd.audio_placements()
    clips_by_track = {}
    for p in placements:
        t_num = p['track']
        clips_by_track.setdefault(t_num, []).append(p)

    # 5. Build DAWproject XML
    root = ET.Element('Project', version='1.0')
    ET.SubElement(root, 'Application', name='logic2daw', version='0.1.0')

    # Transport
    transport = ET.SubElement(root, 'Transport')
    ET.SubElement(transport, 'Tempo', value=str(tempo))
    ET.SubElement(transport, 'TimeSignature', numerator=str(ts_num), denominator=str(ts_den))

    # Structure
    structure = ET.SubElement(root, 'Structure')

    # Master Output Channel (Stereo Out) - Unmutes all tracks in Cubase
    master_chan = ET.SubElement(structure, 'Channel', role='master', audioChannels='2', id='master_out', name='Stereo Out', color='#90a0b0ff')
    ET.SubElement(master_chan, 'Mute', value='false', name='Mute')
    ET.SubElement(master_chan, 'Pan', value='0.5', unit='normalized', min='0', max='1', name='Pan')
    ET.SubElement(master_chan, 'Volume', value='1', unit='linear', min='0', max='2', name='Volume')

    # Regular Audio Tracks routed to master_out
    for t_num in sorted(track_names.keys()):
        t_id = f'track_{t_num}'
        t_el = ET.SubElement(structure, 'Track', id=t_id, name=track_names[t_num], contentType='audio')
        ch = ET.SubElement(t_el, 'Channel', role='regular', audioChannels='2', id=f'chan_{t_num}', name=track_names[t_num], destination='master_out')
        ET.SubElement(ch, 'Mute', value='false', name='Mute')
        ET.SubElement(ch, 'Pan', value='0.5', unit='normalized', min='0', max='1', name='Pan')
        ET.SubElement(ch, 'Volume', value='1', unit='linear', min='0', max='2', name='Volume')

    # Arrangement
    arrang = ET.SubElement(root, 'Arrangement')
    master_lanes = ET.SubElement(arrang, 'Lanes', timeUnit='seconds')
    used_wav_files = set()

    for t_num in sorted(track_names.keys()):
        t_id = f'track_{t_num}'
        track_lanes = ET.SubElement(master_lanes, 'Lanes', track=t_id)
        clips_container = ET.SubElement(track_lanes, 'Clips')

        track_clips = clips_by_track.get(t_num, [])
        for p in track_clips:
            # 1. Exact Start Time in Beats
            start_ticks = max(0, p['pos'] - 34560)
            start_beats = round(start_ticks / 960.0, 6)
            clip_time_str = str(int(start_beats) if start_beats.is_integer() else start_beats)

            reg_idx = p['region_index']
            slots = slots_by_idx.get(reg_idx)
            if not slots:
                continue

            # 2. Exact WAV filename from lFuA record
            wav_filename = None
            if 'lFuA' in slots:
                r = pd.records[slots['lFuA']]
                nlen = struct.unpack_from('<H', r.raw, 0x24 + 0x08)[0]
                wav_filename = r.raw[0x24 + 0x0a : 0x24 + 0x0a + nlen * 2].decode('utf-16le', 'ignore')

            if not wav_filename:
                continue

            disk_wav = logicx_dir / 'Media' / 'Audio Files' / wav_filename
            used_wav_files.add(disk_wav)

            # 3. Exact Trimmed Clip Duration from gRuA record (sample_len)
            sample_len = 0
            if 'gRuA' in slots:
                gr = pd.records[slots['gRuA']]
                sample_len = struct.unpack_from('<I', gr.raw, 0x24 + pd.GRUA_SAMPLELEN_OFF)[0]

            duration_sec = round(sample_len / float(sample_rate), 6) if sample_len > 0 else 2.0
            clip_name = Path(wav_filename).stem

            # 2-Level Clip Hierarchy for Cubase
            outer_clip = ET.SubElement(clips_container, 'Clip', time=clip_time_str, duration=str(duration_sec), fadeTimeUnit='seconds', name=clip_name, enable='true')
            nested_clips = ET.SubElement(outer_clip, 'Clips')
            inner_clip = ET.SubElement(nested_clips, 'Clip', contentTimeUnit='seconds', time='0', duration=str(duration_sec))
            audio_el = ET.SubElement(inner_clip, 'Audio', sampleRate=str(sample_rate), channels='2', duration=str(duration_sec))
            ET.SubElement(audio_el, 'File', path=f'audio/{wav_filename}', external='false')

    # Metadata XML
    meta_root = ET.Element('MetaData', version='1.0')
    ET.SubElement(meta_root, 'Title').text = logicx_dir.stem

    ET.indent(root, space='  ')
    ET.indent(meta_root, space='  ')

    print(f'Packaging into {output_file.name}...')
    with zipfile.ZipFile(output_file, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('project.xml', ET.tostring(root, encoding='utf-8', xml_declaration=True))
        z.writestr('metadata.xml', ET.tostring(meta_root, encoding='utf-8', xml_declaration=True))

        for wav_path in used_wav_files:
            if wav_path.exists():
                z.write(wav_path, arcname=f'audio/{wav_path.name}')

    print(f'\n[SUCCESS] Created {output_file}')
    print(f'  All tracks routed to Stereo Out. Real WAVs & trimmed durations assigned.')

if __name__ == '__main__':
    in_path = sys.argv[1] if len(sys.argv) > 1 else r'C:\dev\daw2logic\Dawprojects\Find a way JP.logicx'
    out_path = sys.argv[2] if len(sys.argv) > 2 else in_path.replace('.logicx', '_from_logic.dawproject')
    convert_logic_to_dawproject(in_path, out_path)
