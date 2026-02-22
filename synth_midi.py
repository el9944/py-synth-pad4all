from config import *
from osc import *
from adsr import *
from mod_osc import *
import rtmidi
from rtmidi.midiutil import open_midiinput
import pyaudio
import time
import numpy as np
from scipy.io.wavfile import write
import sys
import os
import logging

class Synth:
    """
    Class that operates the synth, handles MIDI signals and audio stream.
    Allows the synth to deliver audio on demand.
    """
    def __init__(self,mono=False,pad4all=False,record=False):    

        # Initialize Midi input 
        self.midi = rtmidi.MidiIn()
        self.ports = self.midi.get_ports()
        self.midi.close_port() 

        # List storing all generators
        self.notes=[]
        
        # Store audio data in real-time
        self.data = np.zeros([BUFFER_LENGTH], dtype = np.int16)

       #Constants
        # Should be true if this script is being run from pad4all.py
        self.pad4all = pad4all      
        # Should be True if you're using monophonic mode
        self.mono = mono
        # Should be True if you're recording
        self.record = record
        # Silent Buffer
        self.silence = np.zeros([BUFFER_LENGTH], dtype = np.int16)
 
       #If record is true, 
        # Store the session. As a maximum to prevent issues.
        self.audio = np.zeros([MAXLENGTH,BUFFER_LENGTH], dtype = np.int16)
        # Change over time to increment audio
        self.write = 0

        #Default values
        self.wave_type=0
            #Map all MIDI configurations to its actual parameters
        self.knobs_map = {
            ATTACK_NOTE   : 0.004,
            DECAY_NOTE    : 1,
            SUSTAIN_NOTE  : 1,
            RELEASE_NOTE  : 0.008,
            DELAY_NOTE    : 0,
            FEEDBACK_NOTE : 0,
            MIX_NOTE      : 0,
            DRIVE_NOTE    : 1,
            SOFTEN_NOTE   : 0,
            GLIDE_NOTE    : 0,
            AMP_NOTE      : 1
        }

    
    def find_input(self):
        """
        Check which MIDI input the synth requires, and automate it.
        If you want to use the synth with your own MIDI port, it let you choose manually.
        """
        for i, name in enumerate(self.ports):
            if LOOPMIDINAME.lower() in name.lower() and self.pad4all:
                self.mi, _ = open_midiinput(i)
                port_found = True   
            elif 'RtMidiOut'.lower() in name.lower():
                self.mi, _ = open_midiinput(i)
                port_found = True   
            else:
                port_found = False  
        
        if not port_found:
            self.mi, _ = open_midiinput() 

   
    def get_samples_poly(self,notes):
        """
        Create a buffer of the wave generators stored in play
        """
        return [sum([next(osc) for _,osc in notes])*0.1 for _ in range(BUFFER_LENGTH)]
    
      
    def fade_out(self,buffer):
        '''
        For monophonic use : apply fade-out to a buffer
        '''
        ramp = np.linspace(1, 0, BUFFER_LENGTH, dtype=np.float64)
        buffer *= ramp
        return buffer
    
    def convert(self, samples,amp=1):
        """
        Convert a list buffer to bytes using int16
        """
        return (amp*np.array(samples, dtype=np.float32)* 32767).astype(np.int16).tobytes()
    
    def noteToFreq(self,note):
        """
        Convert a MIDI note to its corresponding frequency
        """
        return (440 / 32) * (2 ** ((note - 9) / 12))
    
    def synth_callback(self):
        """       
        Run continuously by audio stream. 
        Update the audio data being heard in real-time.
        """
        #Monophonic
        if self.mono:
            if len(self.notes) > 1:
                if self.notes[-1][1].triggered:
                    self.data=self.fade_out(self.get_samples_poly([self.notes[-1]]))
                    self.notes[-1][1].ended = True  
                
                elif self.notes[-1][1].val==0 and not self.notes[-2][1].faded:
                    self.data=self.fade_out(self.get_samples_poly([self.notes[-2]]))
                    if self.notes[-2][1].triggered:
                        self.notes[-2][1].ended = True
                    else:
                        self.notes[-2][1].switch_to_ads() 
                    
                    self.notes[-2][1].faded = True
                        
                else:
                    self.data=self.get_samples_poly([self.notes[-1]])
                    
                self.notes = [item for item in self.notes if not(item[1].triggered)]
                    
            elif len(self.notes)==1:
                self.data=self.get_samples_poly([self.notes[-1]]) 
            else:
                self.data=self.silence
       
        else:
        #Polyphonic
            if self.notes:
                self.data=self.get_samples_poly(self.notes)
            else:
                self.data=self.silence
        
        
        self.data = self.convert(self.data)

        if self.record and self.write < len(self.audio):
            self.audio[self.write, :] = np.frombuffer(self.data, dtype=np.int16)
            self.write += 1


    def stream_callback(self,in_data, frame_count, time_info, status):
        """       
        Normalize synth_callback for pyaudio
        """
        self.synth_callback()
        return (self.data, pyaudio.paContinue)
    
    def _init_stream(self):
        """
        Initialize the Stream object.
        """
        self.stream = pyaudio.PyAudio().open(
            rate=SAMPLE_RATE,
            channels=1,
            format=pyaudio.paInt16,
            output=True,
            frames_per_buffer=BUFFER_LENGTH,
            stream_callback=self.stream_callback
        )

    def synth_play(self):
        """
        Remove generator once it is done
        """
        if self.notes:
            self.notes = [item for item in self.notes if not item[1].ended]

    def midi_callback(self,msg,data):
        """
        Run continuously by rtmidi. 
        Interpret incoming MIDI signals, if any.   
        """

        (status, note, vel) = msg[0]
        logging.debug(msg[0])
        
        #Keys
        if status==NOTE_RELEASED:
            element = [item for item in self.notes if item[0]==note]
            element[len(element)-1][1].switch_to_r()
        
        elif status==NOTE_PRESSED:
            self.notes.append((note,
                               iter(ModulatedOscillator(
                                        Oscillator(self.wave_type,self.noteToFreq(note),self.knobs_map[AMP_NOTE]),
                                        EnveloppeADSR(self.knobs_map[ATTACK_NOTE],
                                                      self.knobs_map[DECAY_NOTE],
                                                      self.knobs_map[SUSTAIN_NOTE],
                                                      self.knobs_map[RELEASE_NOTE]),
                                        self.knobs_map[DELAY_NOTE],
                                        self.knobs_map[FEEDBACK_NOTE],
                                        self.knobs_map[MIX_NOTE],
                                        self.knobs_map[GLIDE_NOTE],
                                        self.knobs_map[DRIVE_NOTE],
                                        self.knobs_map[SOFTEN_NOTE]
                                        ))
                            ))
            
  
        #Wave Type Knob
        if status==KNOBS_STATUS and note==WAVETYPE_NOTE and vel==127:
            self.wave_type+= 1
            if self.wave_type==4:
                self.wave_type=0

        #Knobs
        if status == KNOBS_STATUS:
            self.knobs_map[note] = vel / 127
            logging.debug(self.knobs_map[note])

    def play_condition(self):
        """
        Do all the necessary initialization
        """
        self._init_stream()
        self.find_input()
        self.mi.set_callback(self.midi_callback)

    def play(self):
        """
        Run the synth
        """
        self.play_condition()
        try:
            print("Starting...")

            while True:
                self.synth_play()
                time.sleep(0.001)

        except KeyboardInterrupt as err:
            if self.record:
                audio_flat = self.audio.flatten()
                filename = "output.wav"
                if not os.path.exists(filename):
                    write(filename, SAMPLE_RATE, audio_flat)
                else:
                    print(f"{filename} already exists. Choose a different name or remove the existing file.")
            print("Stopping...")



def was_run_by_subprocess():
    return "--pad4all" in sys.argv

if __name__ == "__main__":
    if was_run_by_subprocess():
        Synth(pad4all=True).play()
    else:
        Synth().play()
