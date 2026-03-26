import struct

HEADER_SIZE = 5

# Protocol format: [1 byte type][4 bytes length (big-endian)][N bytes body]

def send_message(sock, msg_type, body):
    """Sends a typed message over sock, handling short-writes."""
    body_bytes = body.encode()
    msg = msg_type.encode() + struct.pack('>I', len(body_bytes)) + body_bytes
    n_sent = 0
    while n_sent < len(msg):
        n = sock.send(msg[n_sent:])
        n_sent += n

def receive_message(sock):
    """Reads a typed message from sock following the protocol format.
    Returns (msg_type, body). Raises OSError if the connection is closed."""
    header = b''
    while len(header) < HEADER_SIZE:
        n_recv = sock.recv(HEADER_SIZE - len(header))
        if not n_recv:
            raise OSError("Connection closed")
        header += n_recv
    
    msg_type = chr(header[0])
    msg_len = struct.unpack('>I', header[1:5])[0]
    msg = b''
    while len(msg) < msg_len:
        msg_recv = sock.recv(msg_len - len(msg))
        if not msg_recv:
            return None
        msg += msg_recv
    return msg_type, msg.decode()
