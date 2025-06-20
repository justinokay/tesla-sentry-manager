# 🚘 Tesla Sentry Merge Tool

This tool automatically merges Tesla Sentry Mode video clips into a clean 2x2 grid layout (Front, Back, Left, Right), encoded with the efficient AV1 codec. It supports large batches, validates inputs, retries failures, and logs errors — all with a friendly progress bar and fast parallel processing.

---

## ✨ Features

- ✅ Merge `-front`, `-back`, `-left_repeater`, and `-right_repeater` clips into a single video
- ✅ 2x2 grid layout with synchronized playback
- ✅ Ultra-efficient AV1 encoding via `libsvtav1`
- ✅ Parallel processing (multi-core)
- ✅ Skips already-processed files
- ✅ Input/output validation with `ffprobe`
- ✅ Retries failed merges (up to 2x)
- ✅ Logs failed merges to `failures.log`
- ✅ Clean green progress bar with ETA
- ✅ Total runtime display

---

## 🧰 Requirements

- Python 3.7+
- FFmpeg installed and available in your system `PATH`
- Python dependencies:
  ```bash
  pip install tqdm
  ```

---

## 🚀 How to Use

### 1. Prepare Your Input Directory

Ensure your TeslaCam files follow the standard naming format:
```
TeslaCam/
├── 2025-06-20_14-25-00-front.mp4
├── 2025-06-20_14-25-00-back.mp4
├── 2025-06-20_14-25-00-left_repeater.mp4
├── 2025-06-20_14-25-00-right_repeater.mp4
...
```

### 2. Run the Script

```bash
python main.py --input /path/to/TeslaCam --output /path/to/output
```

#### Example:
```bash
python main.py --input /Volumes/BLACKED/TeslaCam --output /Volumes/BLACKED/output
```

---

## 🧪 Output

The script will create a merged file for each complete 4-angle timestamp in the output folder:

```
output/
├── 2025-06-20_14-25-00.mp4
├── 2025-06-20_14-30-00.mp4
└── failures.log  # Only created if any clip fails to merge
```

Each video is a 2x2 grid in this layout:

```
+----------+----------+
|  Front   |  Back    |
+----------+----------+
|  Left    |  Right   |
+----------+----------+
```

---

## 🛠️ Options

| Flag         | Description                          | Example                                  |
|--------------|--------------------------------------|------------------------------------------|
| `--input`    | Directory containing raw Tesla clips | `--input /Volumes/SD/TeslaCam`      |
| `--output`   | Directory to save merged videos      | `--output /Volumes/SD/output`       |

---

## 💡 Tips

- Re-runs are safe: the tool skips any output that’s already valid
- If any files fail after retrying, they’ll be logged in `failures.log`
- For best performance, run on SSDs with a fast multi-core CPU (AV1 is CPU-intensive)

---

## 🔐 License

MIT — free for personal or commercial use.

---

## ❤️ Contribute

Want to add:
- GUI support?
- Export to YouTube or cloud?
- Config file?

PRs welcome! Let's make this even better 🚀
