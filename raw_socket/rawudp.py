import socket
from ctypes import create_string_buffer
from struct import pack_into, unpack, calcsize, pack

from utils import checksum

UDP_FMT = '!HHHH'


class UDPDatagram:
    '''
    Simple Python model for an IP datagram
    '''

    def __init__(self, udp_src_port, udp_dst_port, data=''):
        # vars for UDP header
        self.udp_src_port = udp_src_port
        self.udp_dst_port = udp_dst_port
        self.udp_tlen = 0
        self.udp_cksum = 0

        self.data = data
        # re-calc the IP datagram total length
        self.udp_tlen = 8 + len(self.data)

    def pack(self):
        udp_header = pack(UDP_FMT,
                          self.udp_src_port, self.udp_dst_port,
                          self.udp_tlen, self.udp_cksum)
        
        udp_datagram = ''.join([udp_header, self.data])
        return udp_datagram

    def unpack(self, udp_dgram):
        udp_header_size = calcsize(UDP_FMT)
        udp_headers = udp_dgram[:udp_header_size]
        udp_fields = unpack(UDP_FMT, udp_headers)
        self.udp_src_port = udp_fields[0]
        self.udp_dst_port = udp_fields[1]
        self.udp_tlen = udp_fields[2]
        self.udp_cksum = udp_fields[3]
        self.data = udp_dgram[udp_header_size:]
