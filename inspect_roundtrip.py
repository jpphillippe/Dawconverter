import zipfile
import xml.etree.ElementTree as ET

with zipfile.ZipFile(r"C:\dev\daw2logic\Dawprojects\Find a way JP_roundtrip.dawproject") as z:
    root = ET.fromstring(z.read("project.xml"))
    
    print("=" * 60)
    print("TRACKS IN STRUCTURE:")
    tracks = root.findall(".//Structure/Track")
    for t in tracks[:10]:
        print(f"  ID: {t.get('id'):<12} | Type: {t.get('contentType'):<6} | Name: {t.get('name')}")
        
    print("\nLANES IN ARRANGEMENT:")
    lanes = root.findall(".//Arrangement//Lanes")
    for l in lanes[:10]:
        tid = l.get('track')
        if tid:
            clips = l.findall(".//Clip")
            first_clip_name = clips[0].get('name') if clips else "No clips"
            print(f"  Lane for {tid:<12} | Clips: {len(clips):<3} | First: {first_clip_name}")
    print("=" * 60)
