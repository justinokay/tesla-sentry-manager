import os
import time
from pathlib import Path
from datetime import datetime
import subprocess
import argparse
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

log_lock = Lock()
failure_log = []
MAX_RETRIES = 2

def convert_to_timestamp(input_str):
    dt = datetime.strptime(input_str, "%Y-%m-%d_%H-%M-%S")
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def is_valid_video(file_path):
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
            print(f"🟥 ffprobe failed for: {file_path}")
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

def build_video_groups(input_dir):
    input_dir = Path(input_dir)
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

    return [(ts, grp) for ts, grp in video_groups.items() if len(grp) == 4]

def run_ffmpeg_merge(timestamp, group, output_dir):
    out_file = Path(output_dir) / f"{timestamp}.mp4"
    if is_valid_video(out_file):
        return f"✅ Skipped: {timestamp}"

    inputs = [group['front'], group['back'], group['left'], group['right']]
    if not all(is_valid_video(f) for f in inputs):
        raise ValueError("❌ Invalid input(s)")

    creation_time = convert_to_timestamp(timestamp)
    cmd = ['ffmpeg', '-y']
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
    subprocess.run(cmd, check=True)
    return f"🎬 Success: {timestamp}"

def merge_with_retry(timestamp, group, output_dir):
    for attempt in range(1, MAX_RETRIES + 2):
        try:
            return run_ffmpeg_merge(timestamp, group, output_dir)
        except Exception as e:
            if attempt > MAX_RETRIES:
                with log_lock:
                    failure_log.append(f"{timestamp}: {str(e)}")
                return f"🟥 Failed after {MAX_RETRIES + 1} attempts: {timestamp}"

def write_failures(log_path):
    if failure_log:
        with open(log_path, "w") as f:
            for line in failure_log:
                f.write(line + "\n")

def main(input_dir, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    jobs = build_video_groups(input_dir)
    print(f"🎞️ Found {len(jobs)} complete video sets to process.\n")

    start_time = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = {executor.submit(merge_with_retry, ts, grp, output_dir): ts for ts, grp in jobs}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing", colour="green", unit="clip"):
            results.append(future.result())

    elapsed = time.time() - start_time
    minutes, seconds = divmod(int(elapsed), 60)
    print(f"\n⏱️ Elapsed Time: {minutes}m {seconds}s\n")

    for r in results:
        print(r)

    write_failures(output_dir / "failures.log")
    if failure_log:
        print(f"\n🛑 Failures logged to: {output_dir / 'failures.log'}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge Tesla Sentry Mode clips into 2x2 AV1-encoded grid.")
    parser.add_argument("--input", required=True, help="Input directory with raw Tesla clips")
    parser.add_argument("--output", required=True, help="Output directory for merged files")
    args = parser.parse_args()

    main(args.input, args.output)