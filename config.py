from os import listdir, path
import pathlib
from rtmidi.midiutil import open_midiinput
import time

"""
Global Variables

"""

SAMPLE_RATE=44100
BUFFER_LENGTH=1024
MAXLENGTH = int(12582912 / BUFFER_LENGTH) #96mb d'audio au total
LENGTH=0
FILES = [str(pathlib.Path(path.abspath('files/' + f))) for f in listdir("files")]
LOOPMIDINAME = "Pad4all"


"""
Midi Connections

"""
#Keys status
NOTE_PRESSED = 144
NOTE_RELEASED = 128

KNOBS_STATUS = 176
PAD_PRESSED = 153

#Wave Type Switch/Knob
WAVETYPE_NOTE = 113

#ADSR knobs
ATTACK_NOTE = 77
DECAY_NOTE = 93
SUSTAIN_NOTE = 73
RELEASE_NOTE = 75

#Delay knobs
DELAY_NOTE=91
MIX_NOTE=72
FEEDBACK_NOTE=79

#Saturation knobs
DRIVE_NOTE=18
SOFTEN_NOTE=19

#Glide knob
GLIDE_NOTE = 76

#AMP knob
AMP_NOTE = 71

#LOOPER
RECORD_1 = 36
RECORD_2 = 38
PLAY_1 = 37
PLAY_2 = 39
RESET = 43
VOL_L = 74

#METRONOME
UP=42
DOWN=41
PLAY=40

"""
Check Midi Connections

"""

def midi_callback(msg,data):
    print(msg)

if __name__ == "__main__":
    mi, _ = open_midiinput()
    mi.set_callback(midi_callback)

    while True:
        time.sleep(0.01)