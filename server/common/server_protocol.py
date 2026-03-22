from common.utils import Bet
import struct

CONFIRMATION_MSG = b'1'

def deserialize_bet(msg):
    fields = msg.decode().split(',')
    return Bet(fields[0], fields[1], fields[2], fields[3], fields[4], fields[5])

def send_confirmation(sock):
    sent = 0
    while sent < len(CONFIRMATION_MSG):
        n = sock.send(CONFIRMATION_MSG[sent:])
        sent += n

def receive_bet(sock):
    len_recv_byte = b''
    while len(len_recv_byte) < 4:
        bytes_recv = sock.recv(4 - len(len_recv_byte))
        if not bytes_recv:
            return None
        len_recv_byte += bytes_recv
    msg_len = struct.unpack('>I', len_recv_byte)[0]
    msg_recv = b''
    while len(msg_recv) < msg_len:
        bytes_recv = sock.recv(msg_len - len(msg_recv))
        if not bytes_recv:
            return None
        msg_recv += bytes_recv
    return deserialize_bet(msg_recv)