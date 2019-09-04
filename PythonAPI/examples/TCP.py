#import threading
import socket

class Client(object):

    def __init__(self,ip, port):
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.ip = ip
        self.port = port
        #self.sock.setblocking(0)
        self.sock.connect((self.ip,self.port))

    def Send(self,data):
        #threading.Thread(target=self.sock.send,args=(data)).start()
        try:
            self.sock.send(data)
        except ConnectionResetError:
            self.sock.connect((self.ip,self.port))
            self.sock.send(data)


    def Stop(self):
        self.sock.close()

        