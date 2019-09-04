import threading
import socket
import numpy as np
import struct

def ReceiverLoop(port,bufferSize,callback):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0',port))
    while(True):
        data, addr = sock.recvfrom(bufferSize)
        #print("Received data from",addr," : ",data.decode())
        callback(data)


class Receiver(object):

    def __init__(self, port, bufferSize, callback):
        self.thread = threading.Thread(target=ReceiverLoop,args=(port,bufferSize,callback))
        self.thread.start()

    def Stop(self):
        self.thread._stop()



class Sender(object):
    MAX_PACKET_DATA_SIZE = 8000

    sock = None

    @staticmethod
    def init() :
        Sender.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

    @staticmethod
    def sendString(message, ip, port) :
        if(Sender.sock is not None) : 
            Sender.sock.sendto(message.encode(),(ip,port))

    @staticmethod
    def sendBytes(frame_id ,message, ip, port) :
        threading.Thread(target=Func,args=(frame_id ,message, ip, port)).start()
        

def Func(frame_id,message,ip,port):
    if(Sender.sock is not None) :
            array = np.frombuffer(message,dtype=np.uint8)
            chunk_pos = 0
            while(array.size != 0):
                ar = array[:Sender.MAX_PACKET_DATA_SIZE]
                data_size = ar.size
                end = struct.pack('iLQ',data_size,frame_id,chunk_pos)+ar.tobytes()
                if(Sender.sock.sendto(end,(ip,port))<=0):
                    print("Packet lost")
                chunk_pos = chunk_pos+ar.size
                array = array[ar.size:]
    

        