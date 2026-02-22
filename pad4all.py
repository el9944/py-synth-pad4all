import subprocess

"""
For windows user:

1. Download loopmidi
2. Open the app
3. On the 'New port-name' field write Pad4all
4. Click on '+'
5. Run this file

"""
p1 = subprocess.Popen(["python", "vkeyboard.py"])
p2 = subprocess.Popen(["python", "looper_midi.py","--pad4all"])

p1.wait()
p2.wait()