import socket
import sys
import select

from utils import*

#CLIENT_CANNOT_CONNECT
#CLIENT_SERVER_DISCONNECTED
#CLIENT_MESSAGE_PREFIX
#CLIENT_WIPE_ME

socket_list = []
channels = {}
#key = name of channel, value = list of client's socket

BUF_SIZE = 1024


class Server(object):
    
    def __init__(self, port):
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("", int(port)))
        self.socket.listen(5)

        #key = client's socket, value = channel the client is in
        self.socketToChannel = {}

        #key = client's socket, value = client's name
        self.socketToName = {}

        #key = client's socket, value = client's address
        self.socketToAddress = {}

        self.socketToBuffer = {}

        self.socketToBoolean = {}        

        socket_list.append(self.socket)

    def padMsg(self, msg):
        tmp = msg
        if len(msg) < MESSAGE_LENGTH:
            num = MESSAGE_LENGTH - len(msg)
            for x in range(num):
                tmp += " "
        return tmp


    def controlMsg(self, msg, sock):
        cMsg = msg.split()
        comm = cMsg[0]
        if "list" in comm:
            lst = ""
            for key, value in channels.items():
                lst += key + "\n"
            sock.send(self.padMsg(lst))
            # sock.send(lst)
        elif "create" in comm:
            if len(cMsg) < 2:
                sock.send(self.padMsg(SERVER_CREATE_REQUIRES_ARGUMENT))
                # sock.send(SERVER_CREATE_REQUIRES_ARGUMENT  + "\n")
            elif cMsg[1] in channels:
                sock.send(self.padMsg(SERVER_CHANNEL_EXISTS.format(cMsg[1])))
                # sock.send(SERVER_CHANNEL_EXISTS.format(cMsg[1]) + "\n")
            else:
                ################################################
                if sock in self.socketToChannel:
                    name = self.socketToName[sock]
                    exitChannel = self.socketToChannel[sock]
                    tempLstOfSockets = channels[exitChannel]
                    tempLstOfSockets.remove(sock)
                    channels[exitChannel] = tempLstOfSockets
                    for receiverSock in tempLstOfSockets:
                        if receiverSock != self.socket and receiverSock != sock:
                            try:
                                receiverSock.send(self.padMsg(SERVER_CLIENT_LEFT_CHANNEL.format(name)))
                                # receiverSock.send(SERVER_CLIENT_LEFT_CHANNEL.format(name) + "\n")
                            except:
                                socket.close()
                                if socket in socket_list:
                                    socket_list.remove(socket)   
                ################################################
                chann = cMsg[1]            
                channels[chann] = [sock]
                self.socketToChannel[sock] = chann
        elif "join" in comm:
            if len(cMsg) < 2:
                sock.send(self.padMsg(SERVER_JOIN_REQUIRES_ARGUMENT))
                # sock.send(SERVER_JOIN_REQUIRES_ARGUMENT)
            elif cMsg[1] not in channels:
                sock.send(self.padMsg(SERVER_NO_CHANNEL_EXISTS.format(cMsg[1])))
                # sock.send(SERVER_NO_CHANNEL_EXISTS.format(cMsg[1])  + "\n")
            else:
                ################################################
                if sock in self.socketToChannel:
                    name = self.socketToName[sock]
                    exitChannel = self.socketToChannel[sock]
                    tempLstOfSockets = channels[exitChannel]
                    tempLstOfSockets.remove(sock)
                    channels[exitChannel] = tempLstOfSockets
                    for receiverSock in tempLstOfSockets:
                        if receiverSock != self.socket and receiverSock != sock:
                            try:
                                receiverSock.send(self.padMsg(SERVER_CLIENT_LEFT_CHANNEL.format(name)))
                                # receiverSock.send(SERVER_CLIENT_LEFT_CHANNEL.format(name) + "\n")
                            except:
                                socket.close()
                                if socket in socket_list:
                                    socket_list.remove(socket)                        
                ################################################

                chann = cMsg[1]
                lstOfSockets = channels.get(chann) #sockets in the channel
                lstOfSockets.append(sock)
                channels[chann] = lstOfSockets
                self.socketToChannel[sock] = chann
                self.broadcast(sock, comm, chann)
        else:
            sock.send(self.padMsg(SERVER_INVALID_CONTROL_MESSAGE.format(msg)))
            # sock.send(SERVER_INVALID_CONTROL_MESSAGE.format(msg)  + "\n")

    def start_server(self):

        try:
            while True:
                ready_to_read,ready_to_write,in_error = select.select(socket_list,[],[],0)
                for sock in ready_to_read:
                    if sock == self.socket:
                        (new_socket, address) = self.socket.accept()
                        socket_list.append(new_socket)
                        self.socketToAddress[new_socket] = address

                        name = new_socket.recv(MESSAGE_LENGTH)
                        if len(name) < MESSAGE_LENGTH:
                            self.socketToBoolean[new_socket] = True
                            self.socketToBuffer[new_socket] = name

                        else:
                            self.socketToBoolean[new_socket] = False
                            self.socketToName[new_socket] = name.rstrip()
                            self.socketToBuffer[new_socket] = ""

                    else:
                        msg = sock.recv(MESSAGE_LENGTH)
                        if not msg:
                            name = self.socketToName.get(sock)
                            if sock in socket_list:
                                socket_list.remove(sock)
                            chann = self.socketToChannel.get(sock)
                            socketsInChannel = channels.get(chann)
                            for receiverSock in socketsInChannel:
                                if receiverSock != sock:
                                    receiverSock.send(self.padMsg(SERVER_CLIENT_LEFT_CHANNEL.format(name)))
                                    # receiverSock.send(SERVER_CLIENT_LEFT_CHANNEL.format(name) + "\n")
                            socketsInChannel.remove(sock)
                            channels[chann] = socketsInChannel
                            sock.close()
                        else:

                            buf = self.socketToBuffer[sock]
                            lengthOfBuffer = len(buf)
                            # msg = sock.recv(MESSAGE_LENGTH)
                            buf += msg
                            if lengthOfBuffer + len(msg) < MESSAGE_LENGTH:
                                self.socketToBuffer[sock] = buf
                                continue
                            else:
                                msg = buf.rstrip() + "\n"
                                self.socketToBuffer[sock] = ""

                            #checking if it is a new client
                            if self.socketToBoolean[sock]:
                                self.socketToBoolean[sock] = False
                                self.socketToName[sock] = msg.rstrip()
                                self.socketToBuffer[sock] = ""
                            elif isControlMsg(msg):
                                self.controlMsg(msg, sock)
                            else:
                                chann = self.socketToChannel.get(sock)
                                self.broadcast(sock, msg, chann)
        except:
            for sock, name in self.socketToName.items():
                sock.close()
            self.socket.close()

    def broadcast(self, sock, msg, channel):
        socketsInChannel = channels.get(channel)

        for socket in socketsInChannel:
            if socket != self.socket and socket != sock:
                try:
                    name = self.socketToName.get(sock)
                    if "join" in msg:
                        socket.send(self.padMsg(SERVER_CLIENT_JOINED_CHANNEL.format(name)))
                        # socket.send(self.padMsg(SERVER_CLIENT_JOINED_CHANNEL.format(name))
                        # socket.send(SERVER_CLIENT_JOINED_CHANNEL.format(name) + "\n")
                    else:
                        socket.send(self.padMsg("[" + name + "] " + msg))
                        # socket.send(self.padMsg("[" + name + "] " + msg))
                        # socket.send("[" + name + "] " + msg)
                except:
                    socket.close()
                    if socket in socket_list:
                        socket_list.remove(socket)

def isControlMsg(msg):
    if msg[0] == '/':
        return True
    return False


def main():
    args = sys.argv
    if len(args) != 2:
        print "Please supply a port."
        sys.exit()
    server = Server(args[1])
    server.start_server();


if __name__ == '__main__':
    main()

