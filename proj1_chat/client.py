import socket
import sys
import select
import time

from utils import*

class Client(object):

    def __init__(self, name, address, port):
        self.name = name
        self.address = address
        self.port = int(port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.channel = None
        self.buffer = ""

    def connect(self):
        self.socket.connect((self.address, self.port))

        name = self.name
        if len(name) < MESSAGE_LENGTH:
            num = MESSAGE_LENGTH - len(name)
            for x in range(num):
                name += " " 
        self.socket.send(name)


    def send(self, message):
        self.socket.send(message)


    def start_client(self):
        sys.stdout.write(CLIENT_MESSAGE_PREFIX)
        # sys.stdout.write('[Me] ')
        sys.stdout.flush()

        while 1:
            socket_list = [sys.stdin, self.socket]
            ready_to_read,ready_to_write,in_error = select.select(socket_list , [], [])

            for sock in ready_to_read:
                if sock == self.socket:

                    msg = sock.recv(MESSAGE_LENGTH)

                    if not msg:
                        print '\n' + CLIENT_SERVER_DISCONNECTED.format(self.address, self.port)
                        sys.exit()
                    else:
                        ################################################    
                        buf = self.buffer
                        lengthOfBuffer = len(buf)
                        buf += msg
                        if lengthOfBuffer + len(msg) < MESSAGE_LENGTH:
                            self.buffer = buf
                            continue
                        else:
                            msg = buf.rstrip() + "\n"
                            if len(msg) < 2:
                                msg = msg.rstrip()
                            self.buffer = ""
                        ################################################
                        sys.stdout.write(CLIENT_WIPE_ME)                        
                        sys.stdout.write('\r' + msg)
                        sys.stdout.write(CLIENT_MESSAGE_PREFIX)
                        # sys.stdout.write('[Me] ')
                        sys.stdout.flush() 
                else:
                    msg = sys.stdin.readline()
                    if not isControlMsg(msg) and self.channel == None:
                        print SERVER_CLIENT_NOT_IN_CHANNEL
                        # print "Not currently in any channel. Must join a channel before sending messages."
                        sys.stdout.write(CLIENT_MESSAGE_PREFIX)
                        # sys.stdout.write('[Me] ')
                        sys.stdout.flush()
                        continue
                    elif isControlMsg(msg):
                        cMsg = msg.split()
                        comm = cMsg[0]
                        if "create" in comm or "join" in comm:
                            if len(cMsg) < 2 and "create" in comm:
                                print SERVER_CREATE_REQUIRES_ARGUMENT
                                sys.stdout.write('\r' + CLIENT_MESSAGE_PREFIX)
                                sys.stdout.flush()
                                continue
                            elif len(cMsg) < 2 and "join" in comm:
                                print SERVER_JOIN_REQUIRES_ARGUMENT
                                sys.stdout.write('\r' + CLIENT_MESSAGE_PREFIX)
                                sys.stdout.flush()
                                continue
                            else:
                                self.channel = cMsg[1]
                    if len(msg) < MESSAGE_LENGTH:
                        num = MESSAGE_LENGTH - len(msg)
                        for x in range(num):
                            msg += " " 
                    self.socket.send(msg)
                    sys.stdout.write('\r' + CLIENT_MESSAGE_PREFIX)
                    sys.stdout.flush()

def isControlMsg(msg):
    if msg[0] == '/':
        return True
    return False


def main():
    args = sys.argv
    if len(args) != 4:
        print "Please supply a name, server address, and port."
        sys.exit()
    try:
        client = Client(args[1], args[2], args[3])
        client.connect()
        client.start_client()
    except:
        print CLIENT_CANNOT_CONNECT.format(args[2], args[3])
        sys.exit()

if __name__ == '__main__':
    print 'Client is ready!!!! :)'
    main()





