#!/usr/bin/env python3
"""Timelapse automation for Raspberry Pi.

Modes:
  - capture: capture one frame (scheduled every 10 min)
  - process: build daily MP4 + email attachment (scheduled at 22:00)
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import os
import re
import smtplib
import subprocess
import sys
import time
import shlex
from email.message import EmailMessage
from pathlib import Path
from typing import Optional

# Paths (override with env vars if needed)
BASE_DIR = Path(os.getenv("TIMELAPSE_BASE_DIR", "/home/pi/timelapse"))
VIDEO_DIR = Path(os.getenv("TIMELAPSE_VIDEO_DIR", str(BASE_DIR / "videos")))
LOG_DIR = Path(os.getenv("TIMELAPSE_LOG_DIR", str(BASE_DIR / "logs")))
LOG_FILE = Path(os.getenv("TIMELAPSE_LOG_FILE", str(LOG_DIR / "timelapse.log")))

# Capture settings
CAMERA_DEVICE = os.getenv("TIMELAPSE_CAMERA_DEVICE", "/dev/video0")
RESOLUTION = os.getenv("TIMELAPSE_RESOLUTION", "1920x1080")
CAPTURE_RETRIES = int(os.getenv("TIMELAPSE_CAPTURE_RETRIES", "3"))
CAPTURE_RETRY_DELAY_SEC = float(os.getenv("TIMELAPSE_CAPTURE_RETRY_DELAY_SEC", "2"))
# Optional extra flags, e.g. "--set brightness=50% --set Contrast=32"
CAMERA_EXTRA_ARGS = os.getenv("TIMELAPSE_CAMERA_EXTRA_ARGS", "")
# Reliable camera controls via v4l2-ctl, comma-separated key=value pairs.
# Example: "exposure_auto=1,exposure_absolute=120,brightness=90,contrast=40"
V4L2_CONTROLS = os.getenv("TIMELAPSE_V4L2_CONTROLS", "")

# Video settings
VIDEO_FRAMERATE = int(os.getenv("TIMELAPSE_VIDEO_FRAMERATE", "24"))

# Retention
RETENTION_DAYS = int(os.getenv("TIMELAPSE_RETENTION_DAYS", "7"))

# SMTP settings (required for process mode)
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)
EMAIL_TO = os.getenv("EMAIL_TO", "")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes", "on"}

IMG_NAME_RE = re.compile(r"img_(\d{4})\.jpg$")


def setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(LOG_FILE),
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    logger = logging.getLogger("timelapse")
    logger.addHandler(logging.StreamHandler(sys.stdout))
    return logger


def day_dir(day: dt.date) -> Path:
    return BASE_DIR / day.isoformat()


def get_next_index(folder: Path) -> int:
    max_i = 0
    for p in folder.glob("img_*.jpg"):
        m = IMG_NAME_RE.match(p.name)
        if m:
            max_i = max(max_i, int(m.group(1)))
    return max_i + 1


def apply_v4l2_controls(logger: logging.Logger) -> None:
    controls = [c.strip() for c in V4L2_CONTROLS.split(",") if c.strip()]
    if not controls:
        return

    cmd = ["v4l2-ctl", "-d", CAMERA_DEVICE]
    for control in controls:
        if "=" not in control:
            logger.warning("Skipping invalid v4l2 control (expected key=value): %s", control)
            continue
        cmd.extend(["-c", control])

    if cmd == ["v4l2-ctl", "-d", CAMERA_DEVICE]:
        return

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("Applied v4l2 controls: %s", ", ".join(controls))
    except FileNotFoundError:
        logger.warning("v4l2-ctl not found. Install v4l-utils to apply TIMELAPSE_V4L2_CONTROLS.")
    except subprocess.CalledProcessError as e:
        logger.warning("Failed to apply v4l2 controls: %s", (e.stderr or e.stdout or str(e)).strip())


def capture_image(logger: logging.Logger, target_day: Optional[dt.date] = None) -> Path:
    today = target_day or dt.date.today()
    folder = day_dir(today)
    folder.mkdir(parents=True, exist_ok=True)

    idx = get_next_index(folder)
    out_file = folder / f"img_{idx:04d}.jpg"

    cmd = [
        "fswebcam",
        "-d",
        CAMERA_DEVICE,
        "-r",
        RESOLUTION,
        "--no-banner",
        str(out_file),
    ]
    if CAMERA_EXTRA_ARGS.strip():
        cmd[1:1] = shlex.split(CAMERA_EXTRA_ARGS)

    for attempt in range(1, CAPTURE_RETRIES + 1):
        try:
            apply_v4l2_controls(logger)
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info("Captured image: %s", out_file)
            return out_file
        except subprocess.CalledProcessError as e:
            logger.warning(
                "Capture attempt %d/%d failed: %s",
                attempt,
                CAPTURE_RETRIES,
                (e.stderr or e.stdout or str(e)).strip(),
            )
            if attempt < CAPTURE_RETRIES:
                time.sleep(CAPTURE_RETRY_DELAY_SEC)

    logger.error("Camera capture failed after %d attempts", CAPTURE_RETRIES)
    raise RuntimeError("Camera capture failed")


def build_video(logger: logging.Logger, target_day: Optional[dt.date] = None) -> Path:
    today = target_day or dt.date.today()
    input_dir = day_dir(today)
    if not input_dir.exists():
        raise FileNotFoundError(f"No image directory found for {today}: {input_dir}")

    count = len(list(input_dir.glob("img_*.jpg")))
    if count == 0:
        raise RuntimeError(f"No images found in {input_dir}")

    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    output = VIDEO_DIR / f"{today.isoformat()}.mp4"

    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(VIDEO_FRAMERATE),
        "-i",
        str(input_dir / "img_%04d.jpg"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(output),
    ]

    subprocess.run(cmd, check=True, capture_output=True, text=True)
    logger.info("Created video (%d images): %s", count, output)
    return output


def send_email_with_attachment(logger: logging.Logger, file_path: Path, target_day: dt.date) -> None:
    required = {
        "SMTP_HOST": SMTP_HOST,
        "SMTP_USER": SMTP_USER,
        "SMTP_PASSWORD": SMTP_PASSWORD,
        "EMAIL_FROM": EMAIL_FROM,
        "EMAIL_TO": EMAIL_TO,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise RuntimeError(f"Missing SMTP/email env vars: {', '.join(missing)}")

    msg = EmailMessage()
    msg["Subject"] = f"Timelapse for {target_day.isoformat()}"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg.set_content("Attached is your daily timelapse video.")

    data = file_path.read_bytes()
    msg.add_attachment(data, maintype="video", subtype="mp4", filename=file_path.name)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=60) as server:
        if SMTP_USE_TLS:
            server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)

    logger.info("Sent email to %s with attachment %s", EMAIL_TO, file_path)


def cleanup_old_images(logger: logging.Logger) -> None:
    if RETENTION_DAYS < 0:
        logger.info("Retention disabled (TIMELAPSE_RETENTION_DAYS < 0)")
        return

    cutoff = dt.date.today() - dt.timedelta(days=RETENTION_DAYS)
    for child in BASE_DIR.iterdir() if BASE_DIR.exists() else []:
        if not child.is_dir():
            continue
        try:
            folder_date = dt.date.fromisoformat(child.name)
        except ValueError:
            continue
        if folder_date <= cutoff:
            for f in child.glob("*"):
                f.unlink(missing_ok=True)
            child.rmdir()
            logger.info("Deleted old image folder: %s", child)


def run_capture(logger: logging.Logger) -> int:
    try:
        capture_image(logger)
        return 0
    except Exception as e:
        logger.exception("Capture job failed: %s", e)
        return 1


def run_process(logger: logging.Logger) -> int:
    today = dt.date.today()
    try:
        video = build_video(logger, today)
        send_email_with_attachment(logger, video, today)
        cleanup_old_images(logger)
        return 0
    except Exception as e:
        logger.exception("Process job failed: %s", e)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Timelapse automation")
    parser.add_argument("mode", choices=["capture", "process"], help="Job to run")
    args = parser.parse_args()

    logger = setup_logging()
    if args.mode == "capture":
        return run_capture(logger)
    return run_process(logger)


if __name__ == "__main__":
    raise SystemExit(main())
