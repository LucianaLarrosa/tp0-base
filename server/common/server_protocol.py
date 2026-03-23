import struct

CONFIRMATION_MSG = b'1'
LENGTH_SIZE = 4

def send_confirmation(sock):
    sent = 0
    while sent < len(CONFIRMATION_MSG):
        n = sock.send(CONFIRMATION_MSG[sent:])
        sent += n

def receive_message(sock):
    len_recv_byte = b''
    while len(len_recv_byte) < LENGTH_SIZE:
        bytes_recv = sock.recv(LENGTH_SIZE - len(len_recv_byte))
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
    return msg_recv.decode()