package common

import (
	"encoding/binary"
	"net"
)

const (
	LengthSize = 4
)

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

func ReceiveConfirmation(conn net.Conn) error {
	len_recv_byte := make([]byte, 1)
	_, err := conn.Read(len_recv_byte)
	return err
}
