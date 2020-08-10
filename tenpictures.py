from picamera import PiCamera

camera = PiCamera()
camera.start_preview()

for i in range(10):
    camera.capture('image{0:04d}.jpg'.format(i))
    
  
camera.stop_preview()
print("Done taking 10 photos!")  
