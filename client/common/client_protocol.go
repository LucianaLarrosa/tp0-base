package common

import (
	"encoding/binary"
	"fmt"
	"net"
)

const (
	LengthSize = 4
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
