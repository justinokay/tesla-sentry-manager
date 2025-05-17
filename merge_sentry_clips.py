import os
from pathlib import Path
from datetime import datetime
import subprocess

def convert_to_timestamp(input_str):
    dt = datetime.strptime(input_str, "%Y-%m-%d_%H-%M-%S")
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def is_valid_video(file_path):
    """Check if a video file exists and is a valid, playable media file."""
    if not os.path.isfile(file_path):
        print(f"🟥 File not found: {file_path}")
        return False

    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries',
             'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(file_path)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        duration = result.stdout.strip()

        if result.returncode != 0:
            print(f"🟥 ffprobe failed with code {result.returncode} for: {file_path}")
            print(f"stderr: {result.stderr.strip()}")
            return False

        if not duration or float(duration) == 0:
            print(f"🟥 Zero duration or unreadable: {file_path}")
            return False

        print(f"🟩 Valid output exists: {file_path}")
        return True

    except Exception as e:
        print(f"🟥 Exception when probing {file_path}: {e}")
        return False
def is_valid_video(file_path):
    """Check if a video file exists and is a valid, playable media file."""
    if not os.path.isfile(file_path):
        print(f"🟥 File not found: {file_path}")
        return False

    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries',
             'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(file_path)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        duration = result.stdout.strip()

        if result.returncode != 0:
            print(f"🟥 ffprobe failed with code {result.returncode} for: {file_path}")
            print(f"stderr: {result.stderr.strip()}")
            return False

        if not duration or float(duration) == 0:
            print(f"🟥 Zero duration or unreadable: {file_path}")
            return False

        print(f"🟩 Valid output exists: {file_path}")
        return True

    except Exception as e:
        print(f"🟥 Exception when probing {file_path}: {e}")
        return False

def find_and_merge_ffmpeg(input_dir, output_dir):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = list(input_dir.rglob("*.mp4"))
    video_groups = {}

    for f in files:
        base = f.stem.replace('-front', '').replace('-back', '').replace('-left_repeater', '').replace('-right_repeater', '')
        if base not in video_groups:
            video_groups[base] = {}
        if "-front" in f.stem:
            video_groups[base]['front'] = f
        elif "-back" in f.stem:
            video_groups[base]['back'] = f
        elif "-left_repeater" in f.stem:
            video_groups[base]['left'] = f
        elif "-right_repeater" in f.stem:
            video_groups[base]['right'] = f

    for timestamp, group in video_groups.items():
        if len(group) == 4:
            out_file = output_dir / f"{timestamp}.mp4"

            # 🛑 Skip if valid output already exists
            if is_valid_video(out_file):
                print(f"✅ Skipping already valid: {out_file.name}")
                continue

            inputs = [group['front'], group['right'], group['left'], group['back']]

            # 🛡️ Optionally validate inputs too (not required, but good practice)
            if not all(is_valid_video(f) for f in inputs):
                print(f"❌ Skipping {timestamp} due to invalid input file(s)")
                continue

            creation_time = convert_to_timestamp(timestamp)
            cmd = ['ffmpeg']
            for f in inputs:
                cmd += ['-i', str(f)]
            cmd += [
                '-filter_complex',
                'nullsrc=size=1920x1080 [base];'
                '[0:v] setpts=PTS-STARTPTS, scale=960x540 [a];'
                '[1:v] setpts=PTS-STARTPTS, scale=960x540 [b];'
                '[2:v] setpts=PTS-STARTPTS, scale=960x540 [c];'
                '[3:v] setpts=PTS-STARTPTS, scale=960x540 [d];'
                '[base][a] overlay=shortest=1 [tmp1];'
                '[tmp1][b] overlay=shortest=1:x=960 [tmp2];'
                '[tmp2][c] overlay=shortest=1:y=540 [tmp3];'
                '[tmp3][d] overlay=shortest=1:x=960:y=540',
                '-metadata', f'creation_time={creation_time}',
                '-c:v', 'libsvtav1',
                '-pix_fmt', 'yuv420p10le',
                str(out_file)
            ]
            print(f"🎬 Encoding: {out_file.name}")
            subprocess.run(cmd, check=True)

# 🔁 Call the function
find_and_merge_ffmpeg("inputPath", "outputPath")