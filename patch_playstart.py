import re
from pathlib import Path

# 1. Update flatten.py to always inherit parent playStart and duration
flat_file = Path('daw2logic/flatten.py')
content = flat_file.read_text(encoding='utf-8')

old_inherit = '''            if parent is not None and parsed.warps and _is_full_span_reference(duration, parsed.warps):
                parent_duration = _float_attr(parent, "duration")
                if parent_duration > 0:
                    duration = parent_duration
                    play_start = _float_attr(parent, "playStart")'''

new_inherit = '''            if parent is not None:
                parent_ps = _float_attr(parent, "playStart")
                if parent_ps > 0:
                    play_start = parent_ps
                parent_dur = _float_attr(parent, "duration")
                if parent_dur > 0:
                    duration = parent_dur'''

if old_inherit in content:
    content = content.replace(old_inherit, new_inherit)
    flat_file.write_text(content, encoding='utf-8')
    print('[OK] Patched flatten.py (Inherit parent playStart & duration)')
else:
    print('[WARN] Target block in flatten.py not found by exact string, checking regex...')
    content = re.sub(
        r'if parent is not None and parsed\.warps.*?(?=out\.append)',
        new_inherit + '\n            ',
        content,
        flags=re.DOTALL
    )
    flat_file.write_text(content, encoding='utf-8')
    print('[OK] Patched flatten.py via regex')

# 2. Update audio.py to convert play_start beats to seconds
aud_file = Path('daw2logic/audio.py')
aud_content = aud_file.read_text(encoding='utf-8')

old_range = '''def content_range_seconds(clip: AudioClip) -> tuple[float, float]:
    \"\"\"Map clip playStart..playStart+duration through warp markers to source seconds.\"\"\"
    if clip.warps:
        t0 = clip.play_start
        t1 = clip.play_start + clip.duration
        return _interp_warp(t0, clip.warps), _interp_warp(t1, clip.warps)
    return clip.play_start, clip.play_start + clip.duration'''

new_range = '''def content_range_seconds(clip: AudioClip, transport: Transport | None = None) -> tuple[float, float]:
    \"\"\"Map clip playStart..playStart+duration through warp markers to source seconds.\"\"\"
    if clip.warps:
        t0 = clip.play_start
        t1 = clip.play_start + clip.duration
        return _interp_warp(t0, clip.warps), _interp_warp(t1, clip.warps)
    # Convert play_start from beats to seconds if transport provided
    ps_sec = beats_to_seconds(clip.play_start, transport) if transport and clip.play_start > 0 else clip.play_start
    dur_sec = beats_to_seconds(clip.duration, transport) if transport and clip.duration > 0 else clip.duration
    return ps_sec, ps_sec + dur_sec'''

aud_content = aud_content.replace(old_range, new_range)
# Update all calls to pass transport
aud_content = aud_content.replace('content_range_seconds(clip)', 'content_range_seconds(clip, transport)')
aud_file.write_text(aud_content, encoding='utf-8')
print('[OK] Patched audio.py (Convert playStart beats to seconds for slicing)')
