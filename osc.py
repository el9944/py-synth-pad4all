from config import *
import numpy as np

class Oscillator:
    """
    Oscillator that generates wave values when iterated.
    Supports sine, triangle, sawtooth, and square waves.
    Supports frequency modulation (glide effects...).
    
    wave_type: (0=sine, 1=triangle, 2=sawtooth, 3=square)
    
    """
    def __init__(self,wave_type: int = 0,freq: float = 440,amp: int = 1):
        

        #Init Frequency
        self.init_freq = freq
        #Should be 0,1,2,3
        self.wave_type = wave_type
        self.amp = amp
        
        # Increment Frequency
        self._f = freq
        # Increment wave value
        self._phase = 0

    @property
    def freq(self):
        return self._f
    
    @freq.setter
    def freq(self, value):
        """
        Run everytime freq get re-defined.
        Set the oscillator frequency and update the step.
        Allows modulation of frequency.
        """
        self._f = value
        self.set_step()

    def set_step(self):
        """Update the step based on the frequency and wave type."""
        if self.wave_type in [0, 3]:  # sine, square: radians step
            self._step = (2 * np.pi * self._f) / SAMPLE_RATE
        else:  # triangle, sawtooth: fractional step
            self._step = self._f / SAMPLE_RATE   
    
    """
    Each generator yields waveform values and updates `_phase` by `_step`.
    """

    def get_sin_oscillator(self):
        while True:
            yield np.sin(self._phase)
            self._phase += self._step


    def get_triangle_oscillator(self):
        while True:
            yield 2 * abs(2 * self._phase - 1) - 1
            self._phase = (self._phase + self._step) % 1.0
    
    def get_sawtooth_oscillator(self):
        while True:
            yield 2 * self._phase - 1 
            self._phase = (self._phase + self._step) % 1.0  
        
    def get_square_oscillator(self):
        while True:    
            yield  1 if np.sin(self._phase) > 0 else -1
            self._phase += self._step
       
    def __iter__(self):
        """
        Prepare the oscillator to be used as an iterator.
        Selects the waveform generator based on wave_type.
        """      
        self.freq = self.init_freq #Initialize step

        g_map = {
            0: self.get_sin_oscillator,
            1: self.get_triangle_oscillator,
            2: self.get_sawtooth_oscillator,
            3: self.get_square_oscillator
        }

        self.stepper = g_map[self.wave_type]()      
        return self
        
    def __next__(self):
        """ Define what happens when next(iter(Oscillator)) """

        return next(self.stepper)*self.amp


