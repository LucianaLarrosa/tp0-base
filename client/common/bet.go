package common

import "fmt"

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
