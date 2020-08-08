from picamera import PiCamera
from os import system

camera = PiCamera()
camera.resolution = (1024, 768)

for i in range(1000):
    camera.capture('image{0:04d}.jpg'.format(i))

system('convert -delay 100 image*.jpg movie.mp4')
print('done')
