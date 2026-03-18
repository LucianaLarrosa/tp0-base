package common

import (
	"encoding/csv"
	"fmt"
	"net"
	"os"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID             string
	ServerAddress  string
	LoopAmount     int
	LoopPeriod     time.Duration
	BatchMaxAmount int
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
	}
	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return err
	}
	c.conn = conn
	return nil
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop(signalChannel chan os.Signal) {
	filepath := fmt.Sprintf("/data/agency-%s.csv", c.config.ID)
	file, err := os.Open(filepath)
	if err != nil {
		log.Criticalf("action: open_file | result: fail | error: %v", err)
		return
	}
	defer file.Close()

	reader := csv.NewReader(file)

	for {
		select {
		case <-signalChannel:
			log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
			return
		default:
			// Continue with the normal execution
		}

		batch := []Bet{}
		for i := 0; i < c.config.BatchMaxAmount; i++ {
			line, err := reader.Read()
			if err != nil {
				break
			}
			batch = append(batch, Bet{
				Agency:     c.config.ID,
				Nombre:     line[0],
				Apellido:   line[1],
				Documento:  line[2],
				Nacimiento: line[3],
				Numero:     line[4],
			})
		}

		if len(batch) == 0 {
			break
		}

		if err := c.createClientSocket(); err != nil {
			return
		}

		// Send the batch to the server
		if err := sendBatch(c.conn, batch); err != nil {
			log.Errorf("action: apuesta_enviada | result: fail | client_id: %v", c.config.ID)
			c.conn.Close()
			return
		}

		if err := ReceiveConfirmation(c.conn); err != nil {
			log.Errorf("action: apuesta_enviada | result: fail | client_id: %v", c.config.ID)
			c.conn.Close()
			return
		}

		log.Infof("action: apuesta_enviada | result: success | client_id: %v", c.config.ID)
		c.conn.Close()

		time.Sleep(c.config.LoopPeriod)

	}
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}
