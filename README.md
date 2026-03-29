# How to Shoot Time-Lapse Videos with Raspberry Pi and a webcam

Automated timelapse system for a Raspberry Pi 5 using a USB camera.  
Captures images every 10 minutes, generates a daily video, and emails it at 10 PM.

<a href="https://youtu.be/bl7EcG-eDjQ">
  <img src="https://raw.githubusercontent.com/carolinedunn/timelapse/master/photos/openclaw RPi-timelapse-play.jpg" width="720" alt="Raspberry Pi Timelapse Tutorial">
</a>

[Raspberry Pi 5 + AI + OpenClaw Timelapse Tutorial](https://youtu.be/bl7EcG-eDjQ)

---

## 🚀 Features

- 📷 Capture images every 10 minutes
- 🎞️ Generate daily timelapse videos using FFmpeg
- 📧 Automatically email the video
- 🔁 Fully automated with cron
- 🧹 Automatic cleanup of old images
- ⚙️ Configurable via environment variables
- 🎛️ Advanced camera tuning via v4l2 controls

---

## 📁 Project Structure

```
/home/pi/timelapse/
├── YYYY-MM-DD/
│   ├── img_0001.jpg
│   ├── img_0002.jpg
│   └── ...
├── videos/
│   ├── YYYY-MM-DD.mp4
├── logs/
│   └── timelapse.log
```

---

## ⚙️ Requirements

Install dependencies:

```bash
sudo apt update
sudo apt install ffmpeg fswebcam v4l-utils python3
```

---

## 🔧 Configuration

Create a `.env` file in your project directory:

```bash
# Timelapse paths
TIMELAPSE_BASE_DIR=/home/pi/timelapse
TIMELAPSE_VIDEO_DIR=/home/pi/timelapse/videos
TIMELAPSE_LOG_DIR=/home/pi/timelapse/logs
TIMELAPSE_LOG_FILE=/home/pi/timelapse/logs/timelapse.log

# Camera
TIMELAPSE_CAMERA_DEVICE=/dev/video0
TIMELAPSE_RESOLUTION=1920x1080
TIMELAPSE_CAPTURE_RETRIES=3
TIMELAPSE_CAPTURE_RETRY_DELAY_SEC=2
TIMELAPSE_CAMERA_EXTRA_ARGS=

# Video
TIMELAPSE_VIDEO_FRAMERATE=24

# Cleanup
TIMELAPSE_RETENTION_DAYS=7

# SMTP / email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_USE_TLS=true
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=your_email@gmail.com

# Camera controls
TIMELAPSE_V4L2_CONTROLS=auto_exposure=1,exposure_time_absolute=5,gain=30
```

⚠️ **Important:**
- Never commit your real `.env` file to GitHub
- Use a Gmail App Password instead of your main password

---

## 🖥️ Usage

### Capture a single image

```bash
python3 timelapse.py capture
```

### Generate video and send email

```bash
python3 timelapse.py process
```

---

## ⏰ Automation (Cron)

Edit crontab:

```bash
crontab -e
```

Add:

```bash
# Capture every 10 minutes
*/10 * * * * /usr/bin/python3 /home/pi/timelapse.py capture

# Process at 10 PM daily
0 22 * * * /usr/bin/python3 /home/pi/timelapse.py process
```

---

## 🎥 Video Generation

Images are stitched using FFmpeg:

```bash
ffmpeg -framerate 24 -i img_%04d.jpg -c:v libx264 -pix_fmt yuv420p output.mp4
```

---

## 📧 Email Delivery

- Uses SMTP with TLS
- Sends daily timelapse video as attachment
- Works with Gmail (App Password required)

---

## 🛠️ Troubleshooting

### Camera issues

```bash
ls /dev/video*
fswebcam test.jpg
```

### FFmpeg not found

```bash
ffmpeg -version
```

### Email issues

- Verify credentials
- Check logs:
  ```
  /home/pi/timelapse/logs/timelapse.log
  ```

---

## 🔒 Security

- Do NOT commit `.env`
- Add to `.gitignore`:

```
.env
```

---

## 🌱 Future Improvements

- Timestamp overlay
- Motion detection
- Cloud uploads (Google Drive / S3)
- Web dashboard

---

## 📜 License

MIT License





# How to Shoot Time-Lapse Videos with Raspberry Pi HQ Camera

Full tutorial published on Tom's Hardware - https://www.tomshardware.com/how-to/raspberry-pi-time-lapse-video

Video tutorial published on Tom's Hardware YouTube channel - https://youtu.be/dk_Cvg_R3mQ

![Sunrise Time-Lapse](https://github.com/carolinedunn/timelapse/blob/master/GIFS/sunrise.gif)


![Raspberry Pi HQ Camera Front](https://github.com/carolinedunn/timelapse/blob/master/photos/front.JPG)
Raspberry Pi 4 with HQ camera

Full tutorial published on Tom's Hardware - https://www.tomshardware.com/how-to/raspberry-pi-time-lapse-video
