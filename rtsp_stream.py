
import cv2
import timeit
import os
import datetime
import sys
from creds import CAMERA_URL

basedir = os.path.dirname(__file__)

if len(sys.argv) > 1:
  picdirname = f"pics-{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}-{sys.argv[1]}"
else:
  picdirname = f"pics-{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"

picdir = os.path.join(basedir, picdirname)

dir_created = False
print("Pictures will be saved inside:", picdir)

#vcap = cv2.VideoCapture(CAMERA_URL)
vcap = cv2.VideoCapture(CAMERA_URL, cv2.CAP_FFMPEG)

last_stamp = None

delays = []
i = 0
SAVED_COUNT = 0
# Caputer an image every 2 seconds
AUTO_CAPUTER_TIME = 2.0

while True:
  i += 1
  start = timeit.default_timer()
  ret, frame_raw = vcap.read()
  delta = timeit.default_timer() - start
  if not ret:
    print("ERRORE!!!", file=sys.stderr)
    break
  delays.append(delta)

  # remove header (i.e. datetime specs)
  frame = frame_raw[frame_raw.shape[0]//10:,:,:]

  cv2.imshow('VIDEO', frame)
  if i % 50 == 0:
    print(f"Stats [{i//50}]:")
    print(f"\tmin: \t{min(*delays)}")
    print(f"\tmax: \t{max(*delays)}")
    print(f"\tavg: \t{sum(delays)/len(delays)}")
    print(f"\tsum: \t{sum(delays)}")
    print(f"\tcount: {len(delays)}")
    print()
    delays.clear()

  key = cv2.waitKey(1)

  if key == ord('q'):
    break

  if key == ord('a'):
    if last_stamp is not None:
      last_stamp = None
    else:
      print("******* A picture will be automaticcally taken every 2 seconds *******")
      last_stamp = timeit.default_timer()

  if key == ord('s') or (last_stamp is not None and timeit.default_timer() - last_stamp >= AUTO_CAPUTER_TIME):
    now = datetime.datetime.now()
    filename = f"pic-{now.strftime('%Y-%m-%d_%H-%M-%S.%f')}.jpg"

    if not dir_created:
      dir_created = True
      os.mkdir(picdir)
      print(f"Created directory '{picdir}'")

    savepath = os.path.join(picdir, filename)
    print(f"Stampa immagine '{filename}' ({savepath})... ", end='')
    cv2.imwrite(savepath, frame)
    print("DONE!")
    print()

    SAVED_COUNT += 1

    if last_stamp is not None:
      last_stamp = timeit.default_timer()

if SAVED_COUNT:
  print(f"Caputerd {SAVED_COUNT} images inside '{os.path.relpath(picdir)}'")
else:
  print("No picture saved!")
