import pyaudio
import math
import random

def Clamp01(value):
    if value < 0 :
        return 0
    elif value > 1:
        return 1
    else:
        return value

class Impact(object):
    MAX_POWER = 3
    MAX_DURATION = 1.5
    FADE_POWER = 5

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
        #print(str(current_time - self.time))
        return (current_time - self.time)<self.duration

    def GetAmplitude(self, current_time):
        return math.pow(1-Clamp01((current_time - self.time)/self.duration),Impact.FADE_POWER) * self.power

class NoiseGenerator(object):

    def __init__(self):
        self.BITRATE = 6000
        self.time = 0.0
        self.pya = pyaudio.PyAudio()
        self.stream = self.pya.open(format = self.pya.get_format_from_width(width=1,unsigned=True),
                    channels=1,
                    rate = self.BITRATE,
                    output=True,
                    stream_callback=self.callback)
        self.stream.start_stream()
        self.impacts = []

    #Return a float between -1 and 1
    def sound_synth(self,t):
        #return math.sin(t * FREQUENCY * math.pi*2)
        return random.random()*2-1

    def get_amplitude(self, current_time):
        amp = 0.0
        for imp in self.impacts :
            amp += imp.GetAmplitude(current_time)
        return amp

    def update_list(self, current_time):
        for imp in self.impacts :
                if not imp.initialized :
                    imp.initialize(current_time)
        self.impacts[:] = [x for x in self.impacts if x.alive(current_time)]


    def callback(self, in_data ,frame_count ,time_info , status):
        data = bytearray(frame_count)
        for i in range(frame_count):
            t = self.time + i/float(self.BITRATE)
            self.update_list(t)
            data[i] = self.clamp_MinusOneOne2Byte(self.sound_synth(t)*self.get_amplitude(t))
        self.time = self.time + frame_count/float(self.BITRATE)
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
        self.pya.terminate()

    def new_impact(self, power):
        self.impacts.append(Impact(power))