import struct

SUCCESS_MSG = b'1'
ERROR_MSG = b'0'
LENGTH_SIZE = 4

def send_success(sock):
    sock.send(SUCCESS_MSG)

def send_error(sock):
    sock.send(ERROR_MSG)

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
    