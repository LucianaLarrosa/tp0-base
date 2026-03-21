package common

import (
	"fmt"
	"net"
	"strconv"
	"strings"
)

type Bet struct {
	Agency     string
	Nombre     string
	Apellido   string
	Documento  string
	Nacimiento string
	Numero     string
}

const (
	MsgTypeBatch = 'B'
	MsgTypeEnd   = 'E'
	MsgTypeQuery = 'Q'
)

func sendMessage(conn net.Conn, msgType byte, body string) error {
	msg := []byte(fmt.Sprintf("%c%04d%s", msgType, len(body), body))

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

func sendBatch(conn net.Conn, batch []Bet) error {
	msg := ""
	for _, bet := range batch {
		msg += fmt.Sprintf("%s,%s,%s,%s,%s,%s\n",
			bet.Agency, bet.Nombre, bet.Apellido, bet.Documento, bet.Nacimiento, bet.Numero)
	}
	return sendMessage(conn, MsgTypeBatch, msg)
}

func sendEnd(conn net.Conn, agencyID string) error {
	return sendMessage(conn, MsgTypeEnd, agencyID)
}

func receiveMessage(conn net.Conn) (byte, string, error) {
	header := make([]byte, 5)
	header_recv := 0
	for header_recv < 5 {
		n, err := conn.Read(header[header_recv:])
		if err != nil {
			return 0, "", err
		}
		header_recv += n
	}

	msgType := header[0]
	msgLen, _ := strconv.Atoi(string(header[1:5]))
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

func queryWinners(conn net.Conn, agencyID string) ([]string, error) {
	if err := sendMessage(conn, MsgTypeQuery, agencyID); err != nil {
		return nil, err
	}
	_, msg, err := receiveMessage(conn)
	if err != nil {
		return nil, err
	}
	if msg == "" {
		return []string{}, nil
	}
	winners := strings.Split(strings.TrimSpace(msg), ",")
	return winners, nil
}

func receiveConfirmation(conn net.Conn) error {
	_, _, err := receiveMessage(conn)
	return err
}
