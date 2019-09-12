#import threading
import socket

class Client(object):

    def __init__(self,ip, port):
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.ip = ip
        self.port = port
        self.sock.connect((self.ip,self.port))

    def Send(self,data):
        self.sock.send(data)

    def Stop(self):
        self.sock.close()

        