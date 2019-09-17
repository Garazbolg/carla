import numpy as np
import cv2

#conversionMatrice = np.array([[ 0.11400,0.50000 ,  -0.08131],[0.58700, -0.33126, -0.41869],[ 0.29900, -0.16874, 0.50000],[0,0,0]])

def BGRA2YUV(bgra):
    #return bgra[:,:,::2].transpose(2,0,1).tobytes()
    array = RGB2YUV(bgra)
    #y = array[:,:,:1].tobytes()
    #uv = array[:,::2,1:].tobytes()
    #return y + uv
    return (array[:,:,:1].tobytes()) + (array[:,::2,1:].tobytes())
    
def RGB2YUV( rgb ):
    #yuv = np.dot(rgb,conversionMatrice)
    #yuv = yuv.astype(np.uint8)
    conversionMatrice = np.array([[ 0.11400,0.50000 ,  -0.08131],[0.58700, -0.33126, -0.41869],[ 0.29900, -0.16874, 0.50000],[0,0,0]])

    yuv = np.dot(rgb,conversionMatrice).astype(np.uint8)
    yuv[:,:,1:]+=128
    return yuv

'''
bgra = np.ndarray((2,2,4),dtype=np.uint8)
bgra[0][0] = [87,0, 109 ,255]
bgra[0][1] = [0,0, 0 ,255]
bgra[1][0] = [255,255, 255 ,255]
bgra[1][1] = [100,200, 10 ,255]

print(bgra)

print(BGRA2YUV(bgra))
#'''