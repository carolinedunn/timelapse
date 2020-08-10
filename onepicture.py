from picamera import PiCamera

camera = PiCamera()
camera.start_preview()

camera.capture('image.jpg')
camera.stop_preview()
print("Done")  
