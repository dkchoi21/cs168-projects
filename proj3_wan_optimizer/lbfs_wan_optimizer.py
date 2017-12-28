import wan_optimizer

from tcp_packet import Packet

import utils

class WanOptimizer(wan_optimizer.BaseWanOptimizer):
    """ WAN Optimizer that divides data into variable-sized
    blocks based on the contents of the file.

    This WAN optimizer should implement part 2 of project 4.
    """

    # The string of bits to compare the lower order 13 bits of hash to
    GLOBAL_MATCH_BITSTRING = '0111011001010'

    def __init__(self):
        wan_optimizer.BaseWanOptimizer.__init__(self)
        # Add any code that you like here (but do not add any constructor arguments).

        self.hash_to_string = {}
        self.string_to_hash = {}

        self.buffer = ""

        #(src,dst) : flow
        self.flow_buffers = {}

        return

    class Flow:

        def __init__(self):
            self.buffer = ""

        def buffer_space(self):
            return len(self.buffer)

    #####################################################

    def buffer_space(self):
        return len(self.buffer)

    #mapping raw_data : hash_data
    def hash_and_store1(self, payload):
        if len(payload) > 0:
            hash_data = utils.get_hash(payload)
            self.string_to_hash[payload] = hash_data

    #mapping hash_data : raw_data
    def hash_and_store2(self, payload):
        if len(payload) > 0:
            hash_data = utils.get_hash(payload)
            self.hash_to_string[hash_data] = payload

    def send_valid_packets(self, src, dest, payload, is_fin, port):
        # make sure to change to MAX_PACKET_SIZE
        lst = self.split(payload, utils.MAX_PACKET_SIZE)

        # final packet.is_fin that has a payload of 0
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

    def split(self, string, num):
        # if len(string) == 0:
        #     return []
        return [string[start:start + num] for start in range(0, len(string), num)]

    #####################################################


    def receive(self, packet):
        """ Handles receiving a packet.

        Right now, this function simply forwards packets to clients (if a packet
        is destined to one of the directly connected clients), or otherwise sends
        packets across the WAN. You should change this function to implement the
        functionality described in part 2.  You are welcome to implement private
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
                fin = False
                if packet.is_fin:
                    fin = True
                self.find_matching_delimiter2(fin, pair)


        else:
            # The packet must be destined to a host connected to the other middlebox
            # so send it across the WAN.

            if pair not in self.flow_buffers:
                flow = self.Flow()
                if packet.is_fin:
                    self.hash_and_store1(packet.payload)
                    self.send(packet, self.wan_port)
                else:
                    flow.buffer += packet.payload
                    self.find_matching_delimiter1(flow, False, pair)
                self.flow_buffers[pair] = flow
            else:
                curr_flow = self.flow_buffers[pair]
                curr_flow.buffer += packet.payload
                fin = False
                if packet.is_fin:
                    fin = True
                self.find_matching_delimiter1(curr_flow, fin, pair)

            # self.send(packet, self.wan_port)


    def find_matching_delimiter2(self, fin, pair):
        window_start_index = 0
        window_end_index = 48
        while True:

            window = self.buffer[window_start_index:window_end_index]
            hash_data = utils.get_hash(window)
            last_n_bits = utils.get_last_n_bits(hash_data, len(self.GLOBAL_MATCH_BITSTRING))
            if last_n_bits == self.GLOBAL_MATCH_BITSTRING:
                block = self.buffer[:window_end_index]

                self.hash_and_store2(block)
                self.send_valid_packets(pair[0], pair[1], block, fin, self.address_to_port[pair[1]])

                self.buffer = self.buffer[window_end_index:]
                return
            #check your hash mappings
            #1. You find a delimiter
            # 2. (You don't find a delimiter or the data is less than 48 bytes)
            # and there is no more incoming data (i.e. the data has been finned)

            if (window_end_index > self.buffer_space() or self.buffer_space() < 48):
                if fin:
                    block = self.buffer
                    self.hash_and_store2(block)
                    self.send_valid_packets(pair[0], pair[1], block, fin, self.address_to_port[pair[1]])
                    self.buffer = ""
                return
            else:
                window_start_index += 1
                window_end_index += 1



    def find_matching_delimiter1(self, curr_flow, fin, pair):
        window_start_index = 0
        window_end_index = 48
        while True:

            window = curr_flow.buffer[window_start_index:window_end_index]
            hash_data = utils.get_hash(window)
            last_n_bits = utils.get_last_n_bits(hash_data, len(self.GLOBAL_MATCH_BITSTRING))
            if last_n_bits == self.GLOBAL_MATCH_BITSTRING:
                block = curr_flow.buffer[:window_end_index]
                if block in self.string_to_hash:
                    hashed = self.string_to_hash[block]
                    packet_to_send = Packet(pair[0], pair[1], False, fin, hashed)
                    self.send(packet_to_send, self.wan_port)
                    # self.send_valid_packets(pair[0], pair[1], hashed, fin, self.wan_port)
                else:
                    self.hash_and_store1(block)
                    self.send_valid_packets(pair[0], pair[1], block, fin, self.wan_port)

                curr_flow.buffer = curr_flow.buffer[window_end_index:]
                return
            #check your hash mappings
            #1. You find a delimiter
            # 2. (You don't find a delimiter or the data is less than 48 bytes)
            # and there is no more incoming data (i.e. the data has been finned)

            if (window_end_index > curr_flow.buffer_space() or curr_flow.buffer_space() < 48):
                if fin:
                    block = curr_flow.buffer

                    if block in self.string_to_hash:
                        hashed = self.string_to_hash[block]
                        packet_to_send = Packet(pair[0], pair[1], False, fin, hashed)
                        self.send(packet_to_send, self.wan_port)
                    else:
                        self.hash_and_store1(block)
                        self.send_valid_packets(pair[0], pair[1], block, fin, self.wan_port)
                    curr_flow.buffer = ""
                return
            else:
                window_start_index += 1
                window_end_index += 1










#Because there are fewer than 48 bytes in the remainder of the stream
# (assuming a fin is sent after the last word above), your WAN optimizer
# shouldn't compute any more hashes, because there are no more 48 byte windows
# to compute a hash over, and the last bytes should be a stored as one block: "o the length of obstinacy".

# So if we specify the two types of hashing in part 2:
# 1) hash the block of data to be sent to opposing WAN optimizer
# 2) hash of sliding 48B window