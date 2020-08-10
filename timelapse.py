from picamera import PiCamera
from os import system
import datetime
import time

tlminutes = 10 #set this to the number of minutes you wish to run your timelapse camera
secondsinterval = 1 #number of seconds delay between each photo taken
fps = 30 #frames per second timelapse video
numphotos = (tlminutes*60)/secondsinterval #number of photos to take
print("number of photos to take = ", numphotos)

dateraw= datetime.datetime.now()
#dateformatted = dateraw.strftime("%Y-%m-%d")
datetimeformat = dateraw.strftime("%Y-%m-%d_%H:%M")
#print("dateformatted=", dateformatted)
print("RPi started taking photos for timelapse at: " + datetimeformat)


camera = PiCamera()
camera.resolution = (1024, 768)

for i in range(numphotos):
    camera.capture('/home/pi/Pictures/image{0:05d}.jpg'.format(i))
    time.sleep(secondsinterval)
print("Taking photos complete.")
print("Please standby as timelapse video is created.")

system('ffmpeg -r {} -f image2 -s 1024x768 -nostats -loglevel 0 -pattern_type glob -i "/home/pi/Pictures/*.jpg" -vcodec libx264 -crf 25  -pix_fmt yuv420p /home/pi/Videos/{}.mp4'.format(fps, datetimeformat))
#system('rm /home/pi/Pictures/*.jpg')
print('Timelapse video is complete. Video saved to /home/pi/Videos/{}.mp4'.format(datetimeformat))
