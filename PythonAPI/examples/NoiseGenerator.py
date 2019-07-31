import pyaudio
import math
import random

def Clamp01(value):
    if value < 0.0 :
        return 0.0
    elif value > 1.0:
        return 1.0
    else:
        return value

class Impact(object):
    MAX_POWER = 200
    MAX_DURATION = 2
    FADE_POWER = 2
    AMP = 2

    def __init__(self,power):
        power = 0 if power < 0 else power
        power = Impact.MAX_POWER if power > Impact.MAX_POWER else power
        self.power = power/Impact.MAX_POWER
        self.initialized = False
        self.time = 0
        self.duration = self.power * Impact.MAX_DURATION

    def initialize(self,current_time) :
        self.time = current_time
        self.initialized = True

    def alive(self,current_time) :
        return (current_time - self.time)<self.duration

    def GetAmplitude(self, current_time):
        return Impact.AMP * math.pow(1-Clamp01((current_time - self.time)/self.duration),Impact.FADE_POWER) * self.power

class SoundSynth(object):
    def __init__(self,synthfnc,ampfnc,bitrate,pya,fpb):
        self.bitrate = bitrate
        self.time = 0.0
        self.synthfnc = synthfnc
        self.ampfnc = ampfnc
        self.stream = pya.open(format = pya.get_format_from_width(width=1,unsigned=True),
                    channels=1,
                    rate = self.bitrate,
                    output=True,
                    frames_per_buffer=fpb,
                    stream_callback=self.callback)
        self.stream.start_stream()

    def callback(self, in_data ,frame_count ,time_info , status):
        data = bytearray(frame_count)
        for i in range(frame_count):
            t = self.time + i/float(self.bitrate)
            data[i] = self.clamp_MinusOneOne2Byte(self.synthfnc(t)* self.ampfnc(t))
        self.time = self.time + frame_count/float(self.bitrate)
        return (bytes(data),pyaudio.paContinue)
    
    def clamp_MinusOneOne2Byte(self, value):
        if value < -1.0 :
            value = -1.0
        if value > 1.0 : 
            value = 1.0
        return int(math.floor(value*127+128))

    def close(self):
        self.stream.stop_stream()
        self.stream.close()

class SoundManager(object):

    #Initialization
    def __init__(self):
        self.pya = pyaudio.PyAudio()

        #Impacts ---
        self.impacts = []
        self.NoiseImpact = SoundSynth(self.impactSynth,self.impactAmp,2048,self.pya,256)

        #Speed -----
        self.velocity = 0.0
        self.MAX_VELOCITY = 300
        self.VELOCITY_MAX_AMPLITUDE = 0.7
        self.NoiseSpeed = SoundSynth(self.speedSynth,self.speedAmp,1024,self.pya,128)

        #Warning ---
        self.warningActive = False
        self.warningFrequency = 110
        self.warningAmpliude = 0.5
        self.SawWarning = SoundSynth(self.warningSynth,self.warningAmp,4069,self.pya,512)


    #Close fonction to end all the sounds
    def close(self):
        self.NoiseImpact.close()
        self.NoiseSpeed.close()
        self.SawWarning.close()

        self.pya.terminate()


    #Impacts ----------------------------------------------------------
    def impactSynth(self,t):
        return random.random()*2-1
    def impactAmp(self,t):
        amp = 0.0
        self.update_list(t)
        for imp in self.impacts :
            amp += imp.GetAmplitude(t)
        return amp
    def new_impact(self, power):
        self.impacts.append(Impact(power))
    def update_list(self, t):
        if self.impacts is not None :
            for imp in self.impacts :
                    if not imp.initialized :
                        imp.initialize(t)
            self.impacts[:] = [x for x in self.impacts if x.alive(t)]
            if self.impacts is None :
                self.impacts = []
        else :
            self.impacts = []


    #Speed --------------------------------------------------------------
    def speedSynth(self,t):
        return random.random()*2-1
    def speedAmp(self,t):
        return Clamp01(self.velocity/self.MAX_VELOCITY)*self.VELOCITY_MAX_AMPLITUDE


    #Warning ------------------------------------------------------------
    def warningSynth(self,t):
        #return random.random()*2-1
        d=t*self.warningFrequency
        return (d-math.floor(d))*2-1
    def warningAmp(self,t):
        return self.warningAmpliude if self.warningActive else 0