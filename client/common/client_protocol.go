package common

import (
	"fmt"
	"net"
)

type Bet struct {
	Nombre     string
	Apellido   string
	Documento  string
	Nacimiento string
	Numero     string
}

func SendBet(bet Bet, conn net.Conn) error {
	msg := fmt.Sprintf("%s,%s,%s,%s,%s",
		bet.Nombre, bet.Apellido, bet.Documento, bet.Nacimiento, bet.Numero)

	len_msg := len(msg)
	n_sent_len, err := conn.Write([]byte(fmt.Sprintf("%04d", len_msg)))
	if err != nil {
		return err
	}
	for n_sent_len < 4 {
		n, err := conn.Write([]byte(fmt.Sprintf("%04d", len_msg)[n_sent_len:]))
		if err != nil {
			return err
		}
		n_sent_len += n
	}

	n_sent, err := conn.Write([]byte(msg))
	for n_sent < len_msg {
		n, err := conn.Write([]byte(msg[n_sent:]))
		if err != nil {
			return err
		}
		n_sent += n
	}
	return err
}

func ReceiveConfirmation(conn net.Conn) error {
	len_recv_byte := make([]byte, 1)
	_, err := conn.Read(len_recv_byte)
	return err
}
