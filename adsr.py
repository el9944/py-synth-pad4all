from config import *
import itertools

class EnveloppeADSR:
  """
  Iterator that shapes the amplitude
  """
  def __init__(self,attack=0.05,decay=0.1,sustain=0.5,release=1):
    
    self.attack = attack * SAMPLE_RATE
    self.decay = decay * SAMPLE_RATE
    self.sustain = sustain
    self.release = release * SAMPLE_RATE
    
    #If adsr is over
    self.ended = False
    #If release on
    self.triggered = False

    #Monophonic state only
    self.faded = False

  def __iter__(self):
    self.val = 0
    self.stepper = self.ADS()
    return self

  def __next__(self):
    self.val = next(self.stepper)
    return self.val


  def ADS(self):
    """
    Generator that handles attack,decay and sustain
    """
    steppers = []
    if self.attack:
        #Starts at 0, increases each increment. Takes attack time to reach 1.
        steppers.append(itertools.count(0, 1/self.attack))
    if self.decay:
        #Starts at 1, when attack iterator is done, decreases each increment. 
        #Takes decay time to reach sustain value.
        steppers.append(itertools.count(1, -(1-self.sustain)/self.decay))
 
    while True:
        if len(steppers) > 0:
            val = next(steppers[0])
            if len(steppers) == 2 and val > 1:
                steppers.pop(0)
                val = next(steppers[0])
            if len(steppers) == 1 and val < self.sustain:
                steppers.pop(0)
                val = self.sustain
        else:
            val = self.sustain
        yield val
       
  def R(self):
    """
    Generator that handles release
    """
    #Starts at previous value, decreases each increment. If no release iterates 0 until buffer is filled
    release_gen = itertools.count(self.val,- self.val/self.release) if self.release else itertools.cycle([0])
    while True:
        val = next(release_gen)
        if val<=0:
            val=0
            self.ended = True
        yield val

   
  #Extern functions to manually switch steppers.
  def switch_to_r(self):
     self.triggered = True
     self.stepper = self.R()
  
  def switch_to_ads(self):
      self.stepper = self.ADS()
