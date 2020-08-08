from picamera import PiCamera

camera = PiCamera()

for i in range(10):
    camera.capture('image{0:04d}.jpg'.format(i))
    
