import socket as s
import os
import random
import fcntl
import struct

from rawarp import ARPPacket
from rawethernet import EthFrame
from rawip import IPDatagram
from rawudp import UDPDatagram


def bitand(a, b):
    response = "" 
    for i in xrange(len(a)):
        response += chr(ord(a[i]) & ord(b[i]))
    return response


class RawSocket:
    def __init__(self, iface):
        # socket setup: 0x0800 EthType only IP
        self.iface = iface
        self.socket = s.socket(s.AF_PACKET, s.SOCK_RAW)
        self.socket.bind((iface, s.SOCK_RAW))
        # IPs
        self.ip_gateway = self._get_gateway_ip(iface)
        self.ip_src = self._get_local_ip(iface)
        # ports
        self.port_src = random.randint(0x7530, 0xffff)
        # MACs
        self.mac_src = self._get_local_mac(iface)
        self.mac_gateway = 0#self._get_gateway_mac(iface)

    def sendto(self, addr, data=''):
        ip, port = addr
        return self._send(ip, port, data)

    def close(self):
        '''
        Tear down the raw socket connection
        '''
        self.socket.close()

    def _get_mask(self, iface):
        mask = fcntl.ioctl(self.socket.fileno(), 35099, struct.pack('256s', iface[:15]))[20:24]
        return mask

    def _get_local_ip(self, iface):
        '''
        Get the IP address of the local interface
        NOTE: IP address already encoded
        '''
        try:
            ip = fcntl.ioctl(self.socket.fileno(), 0x8915,
                             struct.pack('256s', iface[:15]))[20:24]
            return ip
        except IOError:
            raise RuntimeError('Cannot get IP address of local interface %s'
                               % iface)

    def _get_local_mac(self, iface):
        '''
        Get tge mac address of the local interface
        NOTE: MAC address already encoded
        '''
        try:
            mac = fcntl.ioctl(self.socket.fileno(), 0x8927,
                              struct.pack('256s', iface[:15]))[18:24]
            return mac
        except IOError:
            raise RuntimeError('Cannot get mac address of local interface %s'
                               % iface)

    def _get_gateway_ip(self, iface):
        '''
        Look up the gateway IP address from /proc/net/route
        '''
        with open('/proc/net/route') as route_info:
            for line in route_info:
                fields = line.strip().split()
                if fields[0] == iface: #and fields[1] == '00000000':
                    return struct.pack('<L', int(fields[2], 16))
            else:
                raise RuntimeError('Cannot find the default gateway Ip ' +
                                   'address in /proc/net/route, please ' +
                                   'pass the correct network interface name')

    def _get_mac(self, ip):
        spa = self.ip_src
        sha = self.mac_src
        tpa = ip
        # pack the ARP broadcast mac address
        tha = struct.pack('!6B',
                          int('FF', 16), int('FF', 16), int('FF', 16),
                          int('FF', 16), int('FF', 16), int('FF', 16))
        # pack ARP request
        arp_packet = ARPPacket(sha=sha, spa=spa, tha=tha, tpa=tpa)
        eth_data = arp_packet.pack()
        # pack Ethernet Frame: 0x0806 wrapping ARP packet
        eth_frame = EthFrame(dest_mac=tha, src_mac=sha, tcode=0x0806,
                             data=eth_data)
        phy_data = eth_frame.pack()
        self.socket.send(phy_data)
        while True:
            data = self.socket.recv(4096)
            eth_frame.unpack(data)
            if eth_frame.eth_tcode == 0x0806:
                break
        arp_packet.unpack(eth_frame.data)
        return arp_packet.arp_sha

    def _get_gateway_mac(self, iface):
        '''
        Query the gateway MAC address through ARP request
        '''
        return self._get_mac(self.ip_gateway)

    def _send(self, ip, port, data=''):
        '''
        Send the given data within a packet the set TCP flags,
        return the number of bytes sent.
        '''
        # build UDP datagram
        udp_datagram = UDPDatagram(udp_src_port=self.port_src,
                                   udp_dst_port=port,
                                   data=data)
        ip_data = udp_datagram.pack()

        # build IP datagram
        ip_dst = s.inet_aton(s.gethostbyname(ip))
        ip_datagram = IPDatagram(ip_src_addr=self.ip_src,
                                 ip_dest_addr=ip_dst,
                                 ip_proto=s.IPPROTO_UDP, # UDP
                                 data=ip_data)
        eth_data = ip_datagram.pack()

        # build Ethernet Frame
        mask = self._get_mask(self.iface)
        send_naddr = bitand(ip_dst, mask)
        self_naddr = bitand(self.ip_src, mask)
        if send_naddr != self_naddr:
            print('sending through gateway')
            dst_mac = self._get_gateway_mac(self.iface)
        else:
            print('sending directly')
            dst_mac = self._get_mac(ip_dst)

        eth_frame = EthFrame(dest_mac=dst_mac,
                             src_mac=self.mac_src,
                             data=eth_data)
        phy_data = eth_frame.pack()
        # send raw data
        return self.socket.send(phy_data)
