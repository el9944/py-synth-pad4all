from config import *
from synth_midi import Synth
import numpy as np
import wave
import sys
import logging

class audioloop:
    """Handle a single loop""" 
    def __init__(self):
        
        self.latency=round((69/1000) * (SAMPLE_RATE/BUFFER_LENGTH))
        self.overshoot=round((500/1000) * (SAMPLE_RATE/BUFFER_LENGTH))
        self.length_factor = 1
        
        #Store loop audio data
        self.main_audio = np.zeros([MAXLENGTH, BUFFER_LENGTH], dtype = np.int16)

        #Iterator
        self.readp = 0 #for playback
        self.length = 0 #calculate audio length

        #Booleans
        self.initialized = False
        self.is_recording = False
        self.is_playing = False
        # True when recording is requested but waiting for the start of the first loop (if any)
        self.is_waiting = False

        self.last_buffer_recorded = 0 #Index
        self.preceding_buffer = np.zeros([BUFFER_LENGTH], dtype = np.int16) #Store last buffer
        self.silence = np.zeros([BUFFER_LENGTH], dtype = np.int16)
        
    
    def fade_in(self,buffer):
        '''fade_in() applies fade-in to a buffer'''
        up_ramp = np.linspace(0, 1, BUFFER_LENGTH)
        np.multiply(buffer, up_ramp, out = buffer, casting = 'unsafe')

    def fade_out(self,buffer):
        '''fade_out() applies fade-out to a buffer '''
        down_ramp = np.linspace(1, 0, BUFFER_LENGTH)
        np.multiply(buffer, down_ramp, out = buffer, casting = 'unsafe')

    def increment_pointers(self):
        '''increments readp (used to read the loop), when it reaches the end, it goes back to 0.'''
        #If end of audio
        if self.readp == self.length - 1:
            self.readp = 0
        else:
            self.readp = self.readp + 1
  
    def initialize(self): 
        '''
        Prepares the newly recorded loop for playback:
        - Create a crossfade between the beginning and the end of the loop to avoid clicks.
        - Set the final loop length based on the very first recorded loop.
            (The length becomes a multiple of the main loop to prevent shifting.)
        '''
        logging.debug('initialize called')

        if self.initialized:
            logging.debug('redundant initialization')
            return
        print('Stop Recording...')
        self.last_buffer_recorded = self.length -1 
     
        #Loop length set-up
        self.length_factor = (int((self.length - self.overshoot) / LENGTH) + 1)
        self.length = self.length_factor * LENGTH
        logging.debug('     length ' + str(self.length))
     
        #Crossfade set-up
        self.fade_out(self.main_audio[self.last_buffer_recorded])
        preceding_buffer_copy = np.copy(self.preceding_buffer)
        self.fade_in(preceding_buffer_copy)
        self.main_audio[self.length - 1, :] += preceding_buffer_copy[:]
        
        #Prevents loop desynchronization by setting the read index to the last recorded buffer.
        self.readp =  (self.last_buffer_recorded + self.latency) % self.length
        
        self.initialized = True
        self.is_playing = True
        self.increment_pointers()
        logging.debug('     read pointer: ',self.readp)

    def add_buffer(self, data):
        '''add_buffer() is in charge of recording, add the last buffer to the uninitialized loop'''
        
        #stop the reccording if loop exceed capacity
        if self.length >= (MAXLENGTH - 1):
            self.length = 0
            print('loop full')
            return
        
        self.main_audio[self.length, :] = np.copy(data)
        self.length = self.length + 1


    def is_restarting(self): 
        """Check if the looper is at the beginning of the main loop"""
        if self.readp == 0:
            return True
        return False
    
    def start_recording(self, previous_buffer):
        """Start recording"""

        self.is_recording = True
        self.is_waiting = False

        #Save last buffer before recording to avoid potential clipping
        self.preceding_buffer = np.copy(previous_buffer)
        print('Recording...')

    def read(self):
        '''Returns an audio buffer ready for playback'''   

        #If not initialized, do nothing    
        if not self.initialized:
            return(self.silence)
        
        #If muted increase indexes
        if not self.is_playing:
            self.increment_pointers()
            return(self.silence)
        
        #Else return the current buffer that will play
        tmp = self.readp
        self.increment_pointers()
        return(self.main_audio[tmp, :])
    

 
    #The last three functions are called when pad are triggered
    def set_recording(self):
        '''Call for a start or stop the recording, depending on loop's state'''

        logging.debug('set_recording called')
        already_recording = False

        #If track was already recording
        if self.is_recording:
            already_recording = True

        #Stop recording
        if self.is_recording and not self.initialized:
            self.initialize()
        self.is_recording = False
        self.is_waiting = False

        #Call for a start recording
        if not already_recording:
            self.is_waiting = True

    def clear(self):
        '''Erase loop'''
        self.main_audio = np.zeros([MAXLENGTH, BUFFER_LENGTH], dtype = np.int16)
        self.initialized = False
        self.is_playing = False
        self.is_recording = False
        self.is_waiting = False
        self.length_factor = 1
        self.length = 0
        self.readp = 0
        self.last_buffer_recorded = 0
        self.preceding_buffer = np.zeros([BUFFER_LENGTH], dtype = np.int16)   
        print("Loop deleted")
        
    def toggle_mute(self): 
        """Turn on/off loop volume"""
        if self.is_playing:
            self.is_playing = False
        else:
            self.is_playing = True

class Looper(Synth):
    """
    Superclass that add a looper.
    """
    def __init__(self, mono=False, pad4all=False):
        super().__init__(mono,pad4all)
        
        self.setup_initialized = False

        #Volume Looper
        self.amp_l = 1
        #Loop stock
        self.loops = [audioloop(),audioloop()]
        #Buffer stock
        self.prev_rec_buffer = np.zeros([BUFFER_LENGTH], dtype = np.int16)

        self.loops_knobs = {
            RECORD_2 : [1,"record"],
            PLAY_2   : [1,"play"],
            RECORD_1 : [0,"record"],
            PLAY_1   : [0,"play"]
        }

    #METRONOME
        #Metronome sounds 
        self.filename = FILES[3]
        self.filename2 = FILES[4]
        self.wf = wave.open(self.filename2, 'rb')
        #Stocked data
        self.data_metro=np.zeros([BUFFER_LENGTH], dtype = np.int16)

        #True if metronome is heard
        self.running=False
        #BPM = Speed of the metronome
        self.bpm=140
        #True if sound of a click is over 
        self.ended = False
        #Count to check if filename 1 or 2 has to be played
        self.cpt=0
        #Count silence time 
        self.silence_counter = 0
        
#METRONOME
    def start_stop_metronome(self):
        if self.running:
            self.running=False
        else:
            self.running=True
    
    def up(self):
        self.bpm += 5

    def down(self):
        self.bpm -= 5

    def metronome_callback(self):
        """
        Handles metronome sound
        """
        #METRONOME AUDIO DATA
        if self.running:
            self.silence_counter += 1

            #If one time isn't over
            if not self.ended:
                self.data_metro = self.wf.readframes(BUFFER_LENGTH)
                
                #If data_metro isn't long enough, it add silence to fit buffer size
                if len(self.data_metro) < BUFFER_LENGTH * 2:
                    self.data_metro += b'\x00' * (BUFFER_LENGTH * 2 - len(self.data_metro))
                    self.ended = True
            else:
                self.data_metro = self.silence

                #If silence is over pass to next time
                if self.silence_counter >= round(60 / self.bpm * SAMPLE_RATE) // BUFFER_LENGTH:
                    self.silence_counter=0
                    self.cpt += 1
                    #If a full 4 time is over play other sound
                    if self.cpt % 4 == 0:
                        self.wf = wave.open(self.filename2, 'rb')
                        self.cpt = 0 
                    else:
                        self.wf = wave.open(self.filename, 'rb')
                    self.ended = False
                    self.data_metro = self.wf.readframes(BUFFER_LENGTH)
        else:
            self.data_metro=self.silence
            self.silence_counter =0
            self.wf = wave.open(self.filename2, 'rb')
            self.ended = False
            self.cpt=0

        self.data_metro = np.right_shift(np.frombuffer(self.data_metro, dtype = np.int16), 2)    
        

    def synth_callback(self):
        """
        Stock audio data, and add loop audio to final audio data.
        """
        super().synth_callback()
        global LENGTH
        #Stores last buffer
        self.prev_rec_buffer = np.right_shift(np.frombuffer(self.data, dtype = np.int16), 2)  
        
        #PRE-RECORDING  
        #True if the looper is at the beginning of the first loop
        if self.loops[0].is_restarting():

            if self.loops[1].is_waiting:
                self.loops[1].start_recording(self.prev_rec_buffer)

            if self.loops[0].is_waiting:
                #If 2nd loop is on
                if self.loops[1].initialized:
                    if self.loops[1].is_restarting():
                        self.loops[0].start_recording(self.prev_rec_buffer)
                else:
                    self.loops[0].start_recording(self.prev_rec_buffer)

        #RECORDING
        for loop in self.loops:
            #Is true if start_recording as been called earlier
            if loop.is_recording:
                #Stock data incoming in a loop
                loop.add_buffer(self.prev_rec_buffer)

                #INITIALISATION
                if not self.setup_initialized:
                    if  LENGTH >= MAXLENGTH:
                        print('Overflow')
                        self.setup_initialized = True
                    else:
                        LENGTH = LENGTH + 1    

        self.metronome_callback()
     
        #The data variable is what we hear and is read by stream_callback
        #Here we update it, to the audio data of the user currently playing we add loops recorded and metronome
        self.data = ((self.prev_rec_buffer).astype(np.int32)[:].astype(np.int16) + (self.amp_l*self.loops[0].read()).astype(np.int32)[:].astype(np.int16) + (self.amp_l*self.loops[1].read()).astype(np.int32)[:].astype(np.int16)) + self.data_metro.astype(np.int32)[:].astype(np.int16)

    def midi_callback(self, msg, data):
        """
        Interpret Looper and Metronome midi signals
        """
        global LENGTH
        (status, note, vel) = msg[0]
        super().midi_callback(msg, data)

        #Volume
        if status==KNOBS_STATUS and note==VOL_L:
            self.amp_l = vel*0.1

        if status==PAD_PRESSED and vel>0:

            if note==PLAY:
                self.start_stop_metronome()
            if note==DOWN:
                self.down()
            if note==UP:
                self.up()   
         
            #Reset the looper  
            if note==RESET and self.setup_initialized:
                print('Setup restarting')
                self.setup_initialized = False
                self.loops = [audioloop(),audioloop()]
                self.prev_rec_buffer = np.zeros([BUFFER_LENGTH], dtype = np.int16)
                LENGTH=0  

            #Mute or Demute loop
            if self.loops_knobs[note][1]=="play":
                self.loops[self.loops_knobs[note][0]].toggle_mute()

            #Record/Stop Record/Delete loop
            if self.loops_knobs[note][1]=="record":
                if self.loops[self.loops_knobs[note][0]].initialized :
                    self.loops[self.loops_knobs[note][0]].clear()   
                else:
                    if not self.setup_initialized and self.loops[self.loops_knobs[note][0]].is_recording:
                        self.setup_initialized = True 
                        print("Setup is initialized")
                    self.loops[self.loops_knobs[note][0]].set_recording()  


def was_run_by_subprocess():
    return "--pad4all" in sys.argv

if __name__ == "__main__":
    if was_run_by_subprocess():
        Looper(pad4all=True).play()
    else:
        Looper().play()


