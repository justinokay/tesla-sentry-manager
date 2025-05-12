import os
from pathlib import Path
from datetime import datetime
import subprocess


def convert_to_timestamp(input_str):
    dt = datetime.strptime(input_str, "%Y-%m-%d_%H-%M-%S")
    return dt.strftime("%Y-%m-%d %H:%M:%S")


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
            creation_time = convert_to_timestamp(timestamp)
            out_file = output_dir / f"{timestamp}.mp4"
            inputs = [group['front'], group['right'], group['left'], group['back']]
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
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-crf', '23',
                '-y', str(out_file)
            ]
            subprocess.run(cmd, check=True)

find_and_merge_ffmpeg("inputPath", "outputPath")
