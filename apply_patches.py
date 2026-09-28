import re
from pathlib import Path

print('Applying all fixes to daw2logic repository...')

# ==============================================================================
# 1. PATCH: third_party/LogicProFormatWriter/logicx/projectdata.py
#    - Skip 24-bit slow waveform loop
#    - Deduplicate WAV files (stop creating 302 copies of electric piano)
# ==============================================================================
pd_file = Path('third_party/LogicProFormatWriter/logicx/projectdata.py')
if pd_file.exists():
    content = pd_file.read_text(encoding='utf-8')
    
    # 1a. Skip slow waveform loop
    if 'def _ensure_wav_lgwv(data: bytes) -> bytes:\n    return data' not in content:
        content = content.replace(
            'def _ensure_wav_lgwv(data: bytes) -> bytes:',
            'def _ensure_wav_lgwv(data: bytes) -> bytes:\n    return data'
        )

    # 1b. Deduplicate audio files in _build_region_specs
    new_build_specs = '''def _build_region_specs(template: "ProjectData", items):
    import wave
    regions, wav_assign, rates = [], [], set()
    wav_cache = {}
    name_counts = {}

    for track, wav, tick in items:
        wav = Path(wav)
        wav_key = str(wav.resolve())

        if wav_key in wav_cache:
            internal, file_size, nframes, framerate, bits, channels = wav_cache[wav_key]
        else:
            with wave.open(str(wav), "rb") as wf:
                nframes, framerate = wf.getnframes(), wf.getframerate()
                bits, channels = wf.getsampwidth() * 8, wf.getnchannels()
            content = _ensure_wav_lgwv(wav.read_bytes())
            file_size = len(content)
            
            internal = wav.name
            if internal in name_counts:
                name_counts[internal] += 1
                internal = f"{wav.stem}_{name_counts[wav.name]}{wav.suffix}"
            else:
                name_counts[internal] = 0

            wav_cache[wav_key] = (internal, file_size, nframes, framerate, bits, channels)
            wav_assign.append((internal, content))
            rates.add(framerate)

        regions.append({"track": int(track), "tick": int(tick), "sample_len": nframes,
                        "region_name": wav.stem, "sample_rate": framerate, "bits": bits,
                        "channels": channels, "internal_name": internal, "file_size": file_size})

    return regions, wav_assign, rates'''

    content = re.sub(
        r'def _build_region_specs\(template: "ProjectData", items\):.*?(?=def _assemble_audio_bundle)',
        new_build_specs + '\n\n\n',
        content,
        flags=re.DOTALL
    )
    pd_file.write_text(content, encoding='utf-8')
    print('  [OK] Patched projectdata.py (Fast wave loop + Deduplication)')
else:
    print('  [FAIL] projectdata.py not found!')

# ==============================================================================
# 2. PATCH: daw2logic/flatten.py
#    - Keep all 152 unwarped audio tracks
# ==============================================================================
flat_file = Path('daw2logic/flatten.py')
if flat_file.exists():
    content = flat_file.read_text(encoding='utf-8')
    new_parse_warps = '''def _parse_warps(clip: ET.Element) -> AudioClip | None:
    warps_el = clip.find("Warps")
    if warps_el is not None:
        audio = warps_el.find("Audio")
        warp_pts = tuple(
            WarpPoint(time=_float_attr(w, "time"), content_time=_float_attr(w, "contentTime"))
            for w in warps_el.findall("Warp")
        )
        warp_time_unit = warps_el.get("timeUnit", "beats")
        content_time_unit = warps_el.get("contentTimeUnit", "seconds")
    else:
        audio = clip.find("Audio")
        warp_pts = ()
        warp_time_unit = "beats"
        content_time_unit = "seconds"

    if audio is None:
        return None
    file_el = audio.find("File")
    if file_el is None or not file_el.get("path"):
        return None
    rate_raw = audio.get("sampleRate")
    ch_raw = audio.get("channels")

    return AudioClip(
        start=0.0,
        duration=_float_attr(clip, "duration"),
        path=file_el.get("path"),
        name=clip.get("name"),
        sample_rate=int(float(rate_raw)) if rate_raw else None,
        channels=int(ch_raw) if ch_raw else None,
        play_start=_float_attr(clip, "playStart"),
        fade_in=_optional_float(clip, "fadeInTime"),
        fade_out=_optional_float(clip, "fadeOutTime"),
        fade_time_unit=clip.get("fadeTimeUnit"),
        warps=warp_pts,
        warp_time_unit=warp_time_unit,
        content_time_unit=content_time_unit,
        algorithm=audio.get("algorithm"),
    )'''

    content = re.sub(
        r'def _parse_warps\(clip: ET\.Element\) -> AudioClip \| None:.*?(?=def _collect_notes)',
        new_parse_warps + '\n\n\n',
        content,
        flags=re.DOTALL
    )
    flat_file.write_text(content, encoding='utf-8')
    print('  [OK] Patched flatten.py (Import all 152 audio tracks)')
else:
    print('  [FAIL] flatten.py not found!')

# ==============================================================================
# 3. PATCH: daw2logic/audio.py
#    - Enable slicing for playStart / source trims (Vox Chop-02)
# ==============================================================================
aud_file = Path('daw2logic/audio.py')
if aud_file.exists():
    content = aud_file.read_text(encoding='utf-8')
    
    # 3a. Update needs_audio_processing
    new_needs = '''def needs_audio_processing(clip: AudioClip, transport: Transport, source: Path) -> bool:
    """True when trim, warp, or time-stretch requires baking a derived WAV."""
    content_start, content_end = content_range_seconds(clip)
    if content_start > _STRETCH_TOLERANCE_SEC:
        return True
    if not clip.algorithm or clip.algorithm == "none":
        return False
    content_sec = max(0.0, content_end - content_start)
    timeline_sec = _timeline_seconds(clip, transport, content_sec)
    return abs(timeline_sec - content_sec) > _STRETCH_TOLERANCE_SEC'''

    content = re.sub(
        r'def needs_audio_processing\(clip: AudioClip, transport: Transport, source: Path\) -> bool:.*?(?=def pass_through_warnings)',
        new_needs + '\n\n\n',
        content,
        flags=re.DOTALL
    )

    # 3b. Fast slicing in prepare_audio_clip
    new_prep = '''def prepare_audio_clip(
    clip: AudioClip,
    source: Path,
    work_dir: Path,
    transport: Transport,
) -> tuple[Path, list[str]]:
    """Slice and prepare audio when trim or time-stretch is needed."""
    warnings: list[str] = []
    total_frames, rate, channels, sampwidth = _read_wav_info(source)

    content_start, content_end = content_range_seconds(clip)
    start_frame = max(0, int(round(content_start * rate)))
    end_frame = min(total_frames, int(round(content_end * rate)))
    if end_frame <= start_frame:
        end_frame = min(total_frames, start_frame + 1)

    with wave.open(str(source), "rb") as wf:
        wf.setpos(start_frame)
        raw = wf.readframes(end_frame - start_frame)
    src_n = end_frame - start_frame

    content_sec = (content_end - content_start) or (src_n / rate)
    timeline_sec = _timeline_seconds(clip, transport, content_sec)
    dst_n = max(1, int(round(timeline_sec * rate)))

    is_time_stretched = clip.algorithm and clip.algorithm != "none" and abs(timeline_sec - content_sec) > _STRETCH_TOLERANCE_SEC
    if is_time_stretched:
        warnings.append(
            f"audio '{clip.name or source.name}': time-stretch ({clip.algorithm}) "
            f"approximated by resampling {content_sec:.3f}s -> {timeline_sec:.3f}s"
        )
        raw = _resample_linear(raw, channels, sampwidth, src_n, dst_n)
    else:
        if dst_n < src_n:
            raw = raw[: dst_n * channels * sampwidth]

    if clip.fade_in or clip.fade_out:
        warnings.append(
            f"audio '{clip.name or source.name}': clip fades not imported "
            f"(fadeIn={clip.fade_in}, fadeOut={clip.fade_out})"
        )

    stem = Path(clip.path).stem
    out = work_dir / (
        f"{stem}_{int(clip.start * 1000)}_{int(clip.play_start * 1000)}"
        f"_{int(content_start * 1000)}.wav"
    )
    _write_wav(out, raw, rate, channels, sampwidth)
    return out, warnings'''

    content = re.sub(
        r'def prepare_audio_clip\(.*?return out, warnings',
        new_prep,
        content,
        flags=re.DOTALL
    )
    aud_file.write_text(content, encoding='utf-8')
    print('  [OK] Patched audio.py (Fast audio slicing for playStart / trims)')
else:
    print('  [FAIL] audio.py not found!')

print('\nAll patches successfully applied!')
