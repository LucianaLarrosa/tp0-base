package common

import (
	"encoding/binary"
	"net"
)

const (
	LengthSize         = 4
	LengthConfirmation = 1
)

// Protocol format: [4 bytes length (big-endian)][N bytes body]
// SendMessage sends a message over conn, handling short-writes.
func SendMessage(msg string, conn net.Conn) error {
	msgBytes := []byte(msg)
	lenBytes := make([]byte, LengthSize)
	binary.BigEndian.PutUint32(lenBytes, uint32(len(msg)))
	total := append(lenBytes, msgBytes...)

	n_sent := 0
	for n_sent < len(total) {
		n, err := conn.Write(total[n_sent:])
		if err != nil {
			return err
		}
		n_sent += n
	}
	return nil
}

// ReceiveMessage reads a 1-byte confirmation response from the server.
// Returns '1' on success, '0' on error.
func ReceiveMessage(conn net.Conn) (byte, error) {
	recv_byte := make([]byte, LengthConfirmation)
	_, err := conn.Read(recv_byte)
	return recv_byte[0], err
}
