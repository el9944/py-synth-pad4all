from config import *
import numpy as np

class ModulatedOscillator:
    """
    Takes an Oscillator and shape its sound using effets and ADSR modulator
    """
    def __init__(self, oscillator, modulator,delay_length=0,delay_feedback_time=0,delay_amp=0,glide_time=0,linear_limit=1,soften=0):
        
        self.oscillator = oscillator
        self.modulator = modulator
        
        """glide effect"""
        #Duration
        self.glide_time = int(glide_time * SAMPLE_RATE)
        #Glide Curve that start at an octave lower and slide to the right frequency in a logarithmic slope
        self.glide_vals = np.logspace(np.log10(self.oscillator.init_freq / 2),np.log10(self.oscillator.init_freq),self.glide_time)
        
        """delay effect"""
        #Amount of delay
        self.delay_length = int(delay_length*SAMPLE_RATE)
        #Effect volume
        self.delay_amp = delay_amp
        #Number of repetited signals
        self.delay_feedback_time = int((delay_feedback_time * 8)*SAMPLE_RATE)
        
        #Store the delay effect. Initialized to the amount of delay
        self.delay_data = [0]*self.delay_length
         
        #True when delay data can start being read
        self.delay_initialized = False
        #Index of delay_data
        self.delay_index = 0
        #True when delay has finished
        self.delay_ended = False

        # Enable delay only if all parameters are valid
        self.delay =  bool(self.delay_length and self.delay_amp and self.delay_feedback_time)
       
        """saturation effect"""
        self.linear_limit = linear_limit
        self.soften = soften
        self.hard_limit = 1
        self.clip_limit = self.linear_limit + self.soften*(self.hard_limit - self.linear_limit)
        
        # Enable saturation if true
        self.saturation = bool(not(self.linear_limit == 1))
     
    def __iter__(self):     
        self.oscillator = iter(self.oscillator)
        self.modulator = iter(self.modulator)
        return self
   
    def switch_to_r(self):
        self.modulator.switch_to_r()

    def switch_to_ads(self):
        self.modulator.switch_to_ads()

    @property
    def ended(self): 
        return self.delay_ended if self.delay else self.modulator.ended
    @property
    def faded(self):
        return self.modulator.faded
    @property
    def triggered(self):
        return self.modulator.triggered

    def _glide(self): 
        """Increment glide slope"""
        if self.glide_time:
            self.oscillator.freq = self.glide_vals[len(self.glide_vals) - self.glide_time]
            self.glide_time -= 1

    def _delay_init(self):
        """Initialized delay data"""
        if not self.delay_initialized:

            #Shape of the feedback amplitude
            self.delay_feedback = self.delay_amp * ((np.linspace(0, 1, self.delay_feedback_time) ** 2)[::-1]) 
      
            #Number of repeated signal
            nb_rep = len(self.delay_feedback) // len(self.delay_data)

            #Stock nb_rep signal and is normalized to delay_feedback length
            self.delay_data = np.array(nb_rep*self.delay_data + [0]*(len(self.delay_feedback) % len(self.delay_data)))

            #Shape delay_date amp with delay_feedback and convert back to list
            self.delay_data = (self.delay_data*self.delay_feedback).tolist()
            
            #Normalized delay_data length to a multiple of buffer length
            if (len(self.delay_data) % BUFFER_LENGTH) != 0:
                self.delay_data += [0]*(len(self.delay_data) % BUFFER_LENGTH)
            self.delay_initialized = True    

    def _soft_clip(self,n):
        amplitude, sign = abs(n), 1 if n >= 0 else -1
        if amplitude <= self.linear_limit:
            return n
        if amplitude >= self.clip_limit:
            return self.hard_limit * sign
        scale = self.hard_limit - self.linear_limit
        x = (amplitude - self.linear_limit) / scale  # normalized (0 to 1)
        compression = np.sin(x * (np.pi / 2))  # smoothly reaches 1
        return (self.linear_limit + compression * scale) * sign

    def __next__(self):

        #Glide:
        self._glide()

        mod_osc_value = next(self.oscillator)*next(self.modulator)
        
        #Delay:
        if self.delay:
            if not self.modulator.ended:
                #Load the effect
                self.delay_data.append(np.copy(mod_osc_value)) 
            else:
                self._delay_init()
        
                mod_osc_value += self.delay_data[self.delay_index] 
            
                if self.delay_index >= len(self.delay_data) -1:
                    self.delay_ended = True
                else:
                    self.delay_index += 1   

        #Saturation:      
        if self.saturation:
            return self._soft_clip(mod_osc_value)
        else:
            return  mod_osc_value
