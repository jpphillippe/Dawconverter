import os
import plistlib
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

base = Path(r"C:\dev\daw2logic\Dawprojects")
orig_daw = base / "eq fx and vst automation test.dawproject"
logic_dir = base / "eq fx and vst automation test.logicx"
round_daw = base / "eq fx and vst automation test_from_logic.dawproject"

print("=" * 70)
print("1. ORIGINAL CUBASE DAWPROJECT")
print("=" * 70)
if not orig_daw.is_file():
    print(f"Error: {orig_daw} not found!")
else:
    with zipfile.ZipFile(orig_daw) as z:
        print(f"Files in container: {z.namelist()[:10]}")
        root = ET.fromstring(z.read("project.xml"))
        tracks = root.findall(".//Structure/Track")
        print(f"Total Tracks in Structure: {len(tracks)}")
        for t in tracks:
            print(f"  Track: '{t.get('name')}' | Type: {t.get('contentType')} | ID: {t.get('id')}")
            # Check devices (EQ, VST)
            devs = [d.tag for d in t.findall(".//Devices/*")]
            print(f"    Devices: {devs}")
        
        # Check clips / automation in arrangement
        clips = root.findall(".//Arrangement//Clip")
        audio = root.findall(".//Arrangement//Audio")
        points = root.findall(".//Arrangement//Points")
        print(f"Arrangement: {len(clips)} Clips, {len(audio)} Audio nodes, {len(points)} Automation point curves")

print("\n" + "=" * 70)
print("2. LOGIC PRO BUNDLE (.logicx)")
print("=" * 70)
if not logic_dir.is_dir():
    print(f"Error: {logic_dir} not found!")
else:
    meta_path = logic_dir / "Alternatives/000/MetaData.plist"
    if meta_path.is_file():
        meta = plistlib.loads(meta_path.read_bytes())
        print(f"MetaData SampleRate: {meta.get('SampleRate')} Hz")
        print(f"AudioFiles count: {len(meta.get('AudioFiles', []))}")
    
    media_audio = logic_dir / "Media/Audio Files"
    if media_audio.is_dir():
        wavs = os.listdir(media_audio)
        print(f"Actual WAV files on disk: {len(wavs)} -> {wavs[:5]}")
    else:
        print("Media/Audio Files directory does NOT exist!")
        
    sidecar = logic_dir / "Media/daw2logic Import"
    if sidecar.is_dir():
        print(f"Sidecar exported files: {[str(p.relative_to(logic_dir)) for p in sidecar.rglob('*') if p.is_file()]}")

print("\n" + "=" * 70)
print("3. ROUNDTRIP DAWPROJECT (_from_logic.dawproject)")
print("=" * 70)
if not round_daw.is_file():
    print(f"Error: {round_daw} not found!")
else:
    with zipfile.ZipFile(round_daw) as z:
        print(f"Files in roundtrip container: {z.namelist()[:10]}")
        try:
            xml_content = z.read("project.xml")
            print(f"project.xml size: {len(xml_content)} bytes")
            root_r = ET.fromstring(xml_content)
            tracks_r = root_r.findall(".//Structure/Track")
            print(f"Total Tracks in Structure: {len(tracks_r)}")
            for t in tracks_r:
                print(f"  Track: '{t.get('name')}' | Type: {t.get('contentType')} | ID: {t.get('id')}")
            clips_r = root_r.findall(".//Arrangement//Clip")
            print(f"Total Clips in Arrangement: {len(clips_r)}")
        except Exception as e:
            print(f"CRITICAL: project.xml failed to parse: {e}")
print("=" * 70)
