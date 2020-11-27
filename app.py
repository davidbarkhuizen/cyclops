from flask import Flask, render_template, Response
import cv2
import time

# --------------------------------------------

import pyaudio

# --------------------------------------------

def genHeader(sampleRate, bitsPerSample, channels, samples):
    datasize = 10240000 # Some veeery big number here instead of: #samples * channels * bitsPerSample // 8
    o = bytes("RIFF",'ascii')                                               # (4byte) Marks file as RIFF
    o += (datasize + 36).to_bytes(4,'little')                               # (4byte) File size in bytes excluding this and RIFF marker
    o += bytes("WAVE",'ascii')                                              # (4byte) File type
    o += bytes("fmt ",'ascii')                                              # (4byte) Format Chunk Marker
    o += (16).to_bytes(4,'little')                                          # (4byte) Length of above format data
    o += (1).to_bytes(2,'little')                                           # (2byte) Format type (1 - PCM)
    o += (channels).to_bytes(2,'little')                                    # (2byte)
    o += (sampleRate).to_bytes(4,'little')                                  # (4byte)
    o += (sampleRate * channels * bitsPerSample // 8).to_bytes(4,'little')  # (4byte)
    o += (channels * bitsPerSample // 8).to_bytes(2,'little')               # (2byte)
    o += (bitsPerSample).to_bytes(2,'little')                               # (2byte)
    o += bytes("data",'ascii')                                              # (4byte) Data Chunk Marker
    o += (datasize).to_bytes(4,'little')                                    # (4byte) Data size in bytes
    return o

FORMAT = pyaudio.paInt16
CHUNK = 1024 #1024
RATE = 44100
bitsPerSample = 16 #16
CHANNELS = 1
wav_header = genHeader(RATE, bitsPerSample, CHANNELS, CHUNK)

audio = pyaudio.PyAudio()

stream = audio.open(format=FORMAT, 
    channels=CHANNELS, 
    rate=RATE, 
    input=True, 
    input_device_index=10, 
    frames_per_buffer=CHUNK)

print("recording...")

# --------------------------------------------

camera = cv2.VideoCapture(0)

capture_width = camera.get(3)
capture_height = camera.get(4)
print(f'resolution: {capture_width} x {capture_height}')

def gen_frames():  
    while True:
        success, frame = camera.read()  # read the camera frame
        if not success:
            print('FAILED')
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
               
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# -------------------------------

@app.route('/audio_feed')
def audio_feed():
    # start Recording
    def sound():
        data = wav_header
        data += stream.read(CHUNK)
        yield(data)
        while True:
            data = stream.read(CHUNK)
            yield(data)

    return Response(sound(), mimetype="audio/x-wav")

# -------------------------------

if __name__ == "__main__":
    app.run(debug=True)

# ----------------

# cv2.namedWindow("test")

# img_counter = 0

# while True:
#     ret, frame = cam.read()
#     if not ret:
#         print("failed to grab frame")
#         break
#     cv2.imshow("test", frame)

#     k = cv2.waitKey(1)
#     if k%256 == 27:
#         # ESC pressed
#         print("Escape hit, closing...")
#         break
#     elif k%256 == 32:
#         # SPACE pressed
#         img_name = "opencv_frame_{}.png".format(img_counter)
#         cv2.imwrite(img_name, frame)
#         print("{} written!".format(img_name))
#         img_counter += 1

# cam.release()

# cv2.destroyAllWindows()