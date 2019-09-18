import threading
import socket
import queue
import YUV

class Client(object):

    def __init__(self,ip, port):
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.ip = ip
        self.port = port
        self.sock.connect((self.ip,self.port))

    def Send(self,data):
        try:
            self.sock.send(data)
        except:
            print("Image not sent")

    def Stop(self):
        self.sock.close()

class ThreadedClient(threading.Thread):
    def __init__(self,ip,port,YUV):
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.ip = ip
        self.port = port
        self.sock.connect((self.ip,self.port))
        self.queue = queue.PriorityQueue(5)
        self.YUV = YUV
        self.lastFrame = 0
        self.active = True
        threading.Thread.__init__(self)


    def run(self):
        while self.active:
            item = self.queue.get()
            if item is None:
                break

            if(item[0]<self.lastFrame):
                try:
                    if(self.YUV):
                        self.sock.send(YUV.BGRA2YUV(item[1]))
                    else:
                        self.sock.send(item[1].tobytes())
                except:
                    print("Image " +str(-item[0]) + " not sent")
                self.lastFrame = item[0]

            self.queue.task_done()

    def Send(self, image, frame_id):
        try:
            self.queue.put_nowait((-frame_id,image))
        except:
            print("rejected from queue")

    def Stop(self):
        if(self.sock is not None):
            self.sock.close()
        self.active = False
