package common

import (
	"encoding/csv"
	"fmt"
	"net"
	"os"
	"strings"
	"time"

	"github.com/op/go-logging"
)

const (
	MsgTypeBatch = 'B'
	MsgTypeEnd   = 'E'
	MsgTypeQuery = 'Q'
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
	maxRetries := 5
	for i := 0; i < maxRetries; i++ {
		conn, err := net.Dial("tcp", c.config.ServerAddress)
		if err == nil {
			c.conn = conn
			return nil
		}
		log.Infof("action: connect | result: in_progress | client_id: %v | attempt: %v", c.config.ID, i+1)
		time.Sleep(500 * time.Millisecond)
	}
	log.Criticalf("action: connect | result: fail | client_id: %v", c.config.ID)
	return fmt.Errorf("Could not connect after %d retries", maxRetries)
}

func (c *Client) queryWinners(conn net.Conn) ([]string, error) {
	if err := sendMessage(conn, MsgTypeQuery, c.config.ID); err != nil {
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

		batch, err := readBatch(reader, c.config.ID, c.config.BatchMaxAmount)
		if err != nil {
			log.Errorf("action: read_file | result: fail | error: %v", err)
			return
		}

		if len(batch) == 0 {
			break
		}

		if err := c.createClientSocket(); err != nil {
			return
		}

		// Send the batch to the server
		if err := sendMessage(c.conn, MsgTypeBatch, serializeBatch(batch)); err != nil {
			log.Errorf("action: batch_enviado | result: fail | client_id: %v", c.config.ID)
			c.conn.Close()
			return
		}

		msgType, _, err := receiveMessage(c.conn)
		if err != nil || msgType == '0' {
			log.Errorf("action: batch_enviado | result: fail | client_id: %v", c.config.ID)
			c.conn.Close()
			return
		}

		log.Infof("action: batch_enviado | result: success | client_id: %v", c.config.ID)
		c.conn.Close()

		select {
		case <-signalChannel:
			log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
			return
		case <-time.After(c.config.LoopPeriod):
		}

	}
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)

	if err := c.createClientSocket(); err != nil {
		return
	}
	if err := sendMessage(c.conn, MsgTypeEnd, c.config.ID); err != nil {
		log.Errorf("action: send_end | result: fail | client_id: %v", c.config.ID)
		c.conn.Close()
		return
	}
	c.conn.Close()

	if err := c.createClientSocket(); err != nil {
		return
	}
	defer c.conn.Close()
	winners, err := c.queryWinners(c.conn)
	if err != nil {
		log.Errorf("action: consulta_ganadores | result: fail | client_id: %v", c.config.ID)
		return
	}
	log.Infof("action: consulta_ganadores | result: success | cant_ganadores: %v", len(winners))
}
