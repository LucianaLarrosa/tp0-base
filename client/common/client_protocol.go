package common

import (
	"encoding/binary"
	"fmt"
	"net"
)

type Bet struct {
	Agency     string
	Nombre     string
	Apellido   string
	Documento  string
	Nacimiento string
	Numero     string
}

func serializeBet(bet Bet) string {
	return fmt.Sprintf("%s,%s,%s,%s,%s,%s",
		bet.Agency, bet.Nombre, bet.Apellido, bet.Documento, bet.Nacimiento, bet.Numero)
}

func SendBet(bet Bet, conn net.Conn) error {
	msg := serializeBet(bet)

	lenBytes := make([]byte, 4)
	binary.BigEndian.PutUint32(lenBytes, uint32(len(msg)))
	n_sent_len := 0
	for n_sent_len < 4 {
		n, err := conn.Write(lenBytes[n_sent_len:])
		if err != nil {
			return err
		}
		n_sent_len += n
	}

	msgBytes := []byte(msg)
	n_sent := 0
	for n_sent < len(msgBytes) {
		n, err := conn.Write(msgBytes[n_sent:])
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
