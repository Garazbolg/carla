import threading
import socket

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

class StringSender(object):
    sock = None

    @staticmethod
    def init() :
        StringSender.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

    @staticmethod
    def send(message, ip, port) :
        if(StringSender.sock is not None) : 
            StringSender.sock.sendto(message.encode(),(ip,port))
        