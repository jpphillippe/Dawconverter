from pathlib import Path

aud_file = Path('daw2logic/audio.py')
content = aud_file.read_text(encoding='utf-8')

# Restore content_range_seconds to use play_start directly as seconds
old_func = '''def content_range_seconds(clip: AudioClip, transport: Transport | None = None) -> tuple[float, float]:
    \"\"\"Map clip playStart..playStart+duration through warp markers to source seconds.\"\"\"
    if clip.warps:
        t0 = clip.play_start
        t1 = clip.play_start + clip.duration
        return _interp_warp(t0, clip.warps), _interp_warp(t1, clip.warps)
    # Convert play_start from beats to seconds if transport provided
    ps_sec = beats_to_seconds(clip.play_start, transport) if transport and clip.play_start > 0 else clip.play_start
    dur_sec = beats_to_seconds(clip.duration, transport) if transport and clip.duration > 0 else clip.duration
    return ps_sec, ps_sec + dur_sec'''

new_func = '''def content_range_seconds(clip: AudioClip, transport: Transport | None = None) -> tuple[float, float]:
    \"\"\"Map clip playStart..playStart+duration through warp markers to source seconds.\"\"\"
    if clip.warps:
        t0 = clip.play_start
        t1 = clip.play_start + clip.duration
        return _interp_warp(t0, clip.warps), _interp_warp(t1, clip.warps)
    # play_start and duration are already in seconds
    return clip.play_start, clip.play_start + clip.duration'''

if old_func in content:
    content = content.replace(old_func, new_func)
    aud_file.write_text(content, encoding='utf-8')
    print('[OK] Restored exact seconds in audio.py')
else:
    print('[WARN] Target not found by exact string, patching...')
    import re
    content = re.sub(r'def content_range_seconds\(.*?\n    return [^\n]+', new_func, content, flags=re.DOTALL)
    aud_file.write_text(content, encoding='utf-8')
    print('[OK] Patched via regex')
