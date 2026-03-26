import struct

LENGTH_SIZE = 4

# Protocol format: [4 bytes length (big-endian)][N bytes body]

def send_message(sock, msg):
    """Sends a raw bytes message over sock."""
    sock.send(msg)

def receive_message(sock):
    """Reads a message from sock following the protocol format.
    Returns the decoded message body, or None if the connection was closed."""
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
    