package common

import (
	"encoding/csv"
	"fmt"
	"io"
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

func serializeBatch(bets []Bet) string {
	msg := ""
	for _, bet := range bets {
		msg += serializeBet(bet) + "\n"
	}
	return msg
}

func readBatch(reader *csv.Reader, agency string, maxAmount int) ([]Bet, error) {
	batch := []Bet{}
	for i := 0; i < maxAmount; i++ {
		line, err := reader.Read()
		if err == io.EOF {
			break
		} else if err != nil {
			return batch, err
		}
		batch = append(batch, Bet{
			Agency:     agency,
			Nombre:     line[0],
			Apellido:   line[1],
			Documento:  line[2],
			Nacimiento: line[3],
			Numero:     line[4],
		})
	}
	return batch, nil
}
