package common

import (
	"encoding/binary"
	"net"
)

const (
	HeaderSize = 5
)

// Protocol format: [1 byte type][4 bytes length (big-endian)][N bytes body]
// sendMessage sends a typed message over conn, handling short-writes.
func sendMessage(conn net.Conn, msgType byte, body string) error {
	bodyBytes := []byte(body)
	lenBytes := make([]byte, 4)
	binary.BigEndian.PutUint32(lenBytes, uint32(len(bodyBytes)))

	msg := append([]byte{msgType}, lenBytes...)
	msg = append(msg, bodyBytes...)

	n_sent := 0
	for n_sent < len(msg) {
		n, err := conn.Write(msg[n_sent:])
		if err != nil {
			return err
		}
		n_sent += n
	}
	return nil
}

// receiveMessage reads a typed message from conn, handling short-reads.
// Returns the message type, body, and any error.
func receiveMessage(conn net.Conn) (byte, string, error) {
	header := make([]byte, HeaderSize)
	header_recv := 0
	for header_recv < HeaderSize {
		n, err := conn.Read(header[header_recv:])
		if err != nil {
			return 0, "", err
		}
		header_recv += n
	}

	msgType := header[0]
	msgLen := int(binary.BigEndian.Uint32(header[1:5]))
	msg := make([]byte, msgLen)
	msg_recv := 0
	for msg_recv < msgLen {
		n, err := conn.Read(msg[msg_recv:])
		if err != nil {
			return 0, "", err
		}
		msg_recv += n
	}
	return msgType, string(msg), nil
}
