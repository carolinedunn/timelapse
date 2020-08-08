from picamera import PiCamera
from os import system
import datetime
import time

dateraw= datetime.datetime.now()
dateformatted = dateraw.strftime("%Y-%m-%d")
datetimeformat = dateraw.strftime("%Y-%m-%d_%H:%M")
print("dateformatted=", dateformatted)
print("datetimeformat= ", datetimeformat)

camera = PiCamera()
camera.resolution = (1024, 768)

for i in range(50):
    camera.capture('/home/pi/Pictures/{}_{}.jpg'.format(dateformatted,i))
    time.sleep(1)

system('convert -delay 10 /home/pi/Pictures/*.jpg {}.mp4'.format(datetimeformat))
system('rm /home/pi/Pictures/*.jpg')
print('done')
