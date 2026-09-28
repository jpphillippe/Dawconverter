import zipfile, re
from pathlib import Path

target = Path(r"C:\dev\daw2logic\Dawprojects\eq fx and vst automation test_from_logic.dawproject")

with zipfile.ZipFile(target, "r") as z:
    xml_content = z.read("project.xml").decode("utf-8", "replace")
    meta_content = z.read("metadata.xml")
    audio_files = {name: z.read(name) for name in z.namelist() if name.startswith("audio/")}

# Clean out invalid control characters from XML
cleaned_xml = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ufffd]", "", xml_content)
# Replace the specific garbled character if it remains
cleaned_xml = cleaned_xml.replace("Smash (R?", "Smash (R)")

with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as z:
    z.writestr("project.xml", cleaned_xml.encode("utf-8"))
    z.writestr("metadata.xml", meta_content)
    for name, data in audio_files.items():
        z.writestr(name, data)

print("Sanitized project.xml successfully!")
