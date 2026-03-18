package common

import (
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

func sendBatch(conn net.Conn, batch []Bet) error {
	msg := ""
	for _, bet := range batch {
		msg += fmt.Sprintf("%s,%s,%s,%s,%s,%s\n",
			bet.Agency, bet.Nombre, bet.Apellido, bet.Documento, bet.Nacimiento, bet.Numero)
	}
	n_sent_len, err := conn.Write([]byte(fmt.Sprintf("%04d", len(msg))))
	if err != nil {
		return err
	}
	for n_sent_len < 4 {
		n, err := conn.Write([]byte(fmt.Sprintf("%04d", len(msg))[n_sent_len:]))
		if err != nil {
			return err
		}
		n_sent_len += n
	}

	n_sent, err := conn.Write([]byte(msg))
	if err != nil {
		return err
	}
	for n_sent < len(msg) {
		n, err := conn.Write([]byte(msg[n_sent:]))
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
