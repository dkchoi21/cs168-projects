import wan_optimizer
from tcp_packet import Packet

import utils

class WanOptimizer(wan_optimizer.BaseWanOptimizer):
    """ WAN Optimizer that divides data into fixed-size blocks.

    This WAN optimizer should implement part 1 of project 4.
    """

    # Size of blocks to store, and send only the hash when the block has been
    # sent previously
    BLOCK_SIZE = 8000

    def __init__(self):
        wan_optimizer.BaseWanOptimizer.__init__(self)
        # Add any code that you like here (but do not add any constructor arguments).

        self.hash_to_string = {}
        self.string_to_hash = {}

        self.buffer = ""

        #(src,dst) : flow
        self.flow_buffers = {}


    class Flow:

        def __init__(self):
            self.buffer = ""

        def buffer_space(self):
            return len(self.buffer)


    #####################################################

    def hash_and_store(self, payload):
        if len(payload) > 0:
            hash_data = utils.get_hash(payload)
            # self.hash_to_string[hash_data] = payload
            self.string_to_hash[payload] = hash_data

    def hash_and_store2(self, payload):
        if len(payload) > 0:
            hash_data = utils.get_hash(payload)
            self.hash_to_string[hash_data] = payload
            # self.string_to_hash[payload] = hash_data

    def buffer_space(self):
        return len(self.get_parent_block())

    def get_parent_block(self):
        block = ""
        for packet in self.buffer:
            block += packet.payload
        return block

    def send_packets_in_buffer(self):
        for prev_packet in self.buffer:
            self.send(prev_packet, self.address_to_port[prev_packet.dest])

    def split(self, string, num):
        # if len(string) == 0:
        #     return []
        return [string[start:start + num] for start in range(0, len(string), num)]

    def buffer_space(self):
        return len(self.buffer)

    def send_valid_packets(self, src, dest, payload, is_fin, port):
        #make sure to change to MAX_PACKET_SIZE
        lst = self.split(payload, utils.MAX_PACKET_SIZE)

        #final packet.is_fin that has a payload of 0
        if len(lst) == 0:
            packet_to_send = Packet(src, dest, True, is_fin, payload)
            self.send(packet_to_send, port)
            return

        for i in range(len(lst)):
            if i == len(lst) - 1:

                packet_to_send = Packet(src, dest, True, is_fin, lst[i])
                self.send(packet_to_send, port)
                return
            packet_to_send = Packet(src, dest, True, False, lst[i])
            self.send(packet_to_send, port)

    #####################################################

    def receive(self, packet):
        """ Handles receiving a packet.

        Right now, this function simply forwards packets to clients (if a packet
        is destined to one of the directly connected clients), or otherwise sends
        packets across the WAN. You should change this function to implement the
        functionality described in part 1.  You are welcome to implement private
        helper fuctions that you call here. You should *not* be calling any functions
        or directly accessing any variables in the other middlebox on the other side of
        the WAN; this WAN optimizer should operate based only on its own local state
        and packets that have been received.
        """

        pair = (packet.src, packet.dest)

        if packet.dest in self.address_to_port:
            # The packet is destined to one of the clients connected to this middlebox;
            # send the packet there.

            if not packet.is_raw_data:
                raw_data_block = self.hash_to_string[packet.payload]
                self.send_valid_packets(packet.src, packet.dest, raw_data_block, packet.is_fin, self.address_to_port[packet.dest])
            else:
                self.buffer += packet.payload
                if self.buffer_space() >= self.BLOCK_SIZE or packet.is_fin:
                    if self.buffer_space() >= self.BLOCK_SIZE and packet.is_fin:

                        full_block = self.buffer[:self.BLOCK_SIZE]
                        small_block = self.buffer[self.BLOCK_SIZE:]

                        self.buffer = ""

                        self.hash_and_store2(full_block)
                        self.send_valid_packets(pair[0], pair[1], full_block, False, self.address_to_port[packet.dest])

                        self.hash_and_store2(small_block)
                        self.send_valid_packets(pair[0], pair[1], small_block, packet.is_fin, self.address_to_port[packet.dest])
                    else:
                        if packet.is_fin:
                            if len(self.buffer) != 0:
                                self.hash_and_store2(self.buffer)
                            self.send_valid_packets(pair[0], pair[1], self.buffer, True, self.address_to_port[packet.dest])
                            self.buffer = ""
                        else:
                            full_block = self.buffer[:self.BLOCK_SIZE]
                            self.buffer = self.buffer[self.BLOCK_SIZE:]
                            self.hash_and_store2(full_block)
                            self.send_valid_packets(pair[0], pair[1], full_block, False, self.address_to_port[packet.dest])

        else:
            # The packet must be destined to a host connected to the other middlebox
            # so send it across the WAN.
            if pair not in self.flow_buffers:
                flow = self.Flow()
                if packet.is_fin:
                    self.hash_and_store(packet.payload)
                    self.send(packet, self.wan_port)
                else:
                    flow.buffer += packet.payload
                self.flow_buffers[pair] = flow
            else:
                curr_flow = self.flow_buffers[pair]
                curr_flow.buffer += packet.payload
                # bytes_sum = curr_flow.buffer_space() + bytes_of_data
                if curr_flow.buffer_space() >= self.BLOCK_SIZE or packet.is_fin:

                    if curr_flow.buffer_space() >= self.BLOCK_SIZE and packet.is_fin:

                        full_block = curr_flow.buffer[:self.BLOCK_SIZE]
                        small_block = curr_flow.buffer[self.BLOCK_SIZE:]

                        curr_flow.buffer = ""

                        if full_block in self.string_to_hash:
                            hash_data = self.string_to_hash[full_block]
                            packet_to_send = Packet(packet.src, packet.dest, False, False, hash_data)
                            self.send(packet_to_send, self.wan_port)
                        else:

                            self.hash_and_store(full_block)
                            self.send_valid_packets(pair[0], pair[1], full_block, False, self.wan_port)

                        if len(small_block) != 0:
                            if small_block in self.string_to_hash:
                                hash_data = self.string_to_hash[small_block]
                                packet_to_send = Packet(packet.src, packet.dest, False, packet.is_fin, hash_data)
                                self.send(packet_to_send, self.wan_port)
                            else:
                                self.hash_and_store(small_block)
                                self.send_valid_packets(pair[0], pair[1], small_block, packet.is_fin, self.wan_port)

                    else:
                        #case where packet.is_fin and buffer is less than block size
                        if packet.is_fin:
                            if curr_flow.buffer in self.string_to_hash:
                                hash_data = self.string_to_hash[curr_flow.buffer]
                                packet_to_send = Packet(packet.src, packet.dest, False, True, hash_data)
                                self.send(packet_to_send, self.wan_port)
                            else:
                                if len(curr_flow.buffer) != 0:
                                    self.hash_and_store(curr_flow.buffer)
                                self.send_valid_packets(pair[0], pair[1], curr_flow.buffer, True, self.wan_port)
                            curr_flow.buffer = ""
                        #case where not packet.is_fin and buffer is equal to or greater than block size
                        else:
                            full_block = curr_flow.buffer[:self.BLOCK_SIZE]
                            curr_flow.buffer = curr_flow.buffer[self.BLOCK_SIZE:]
                            if full_block in self.string_to_hash:
                                hash_data = self.string_to_hash[full_block]
                                packet_to_send = Packet(packet.src, packet.dest, False, False, hash_data)
                                self.send(packet_to_send, self.wan_port)
                            else:

                                if len(full_block) > 0:
                                    hash_data = utils.get_hash(full_block)

                                    # self.hash_to_string[hash_data] = payload
                                    self.string_to_hash[full_block] = hash_data
                                self.send_valid_packets(pair[0], pair[1], full_block, False, self.wan_port)










