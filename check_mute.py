import zipfile
import xml.etree.ElementTree as ET

# 1. Check original DAWproject for the RHodes track and its clips
with zipfile.ZipFile(r"C:\dev\daw2logic\Dawprojects\Find a way JP.dawproject") as z:
    root = ET.fromstring(z.read("project.xml"))
    
    # Find RHodes track ID
    rhodes_id = None
    for t in root.findall(".//Structure/Track"):
        if "rhodes" in t.get("name", "").lower():
            rhodes_id = t.get("id")
            print(f"Original RHodes Track: {t.get('name')} (ID: {rhodes_id})")
            break
            
    if rhodes_id:
        for lane in root.findall(".//Arrangement//Lanes"):
            if lane.get("track") == rhodes_id:
                clips = lane.findall(".//Clip")
                print(f"Total clips on RHodes: {len(clips)}")
                if clips:
                    print("Sample RHodes clip XML attributes:")
                    print(clips[0].attrib)
                    break
