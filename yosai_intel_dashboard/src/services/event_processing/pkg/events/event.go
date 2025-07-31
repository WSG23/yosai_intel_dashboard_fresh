package events

import "encoding/json"

// Event represents a generic domain event consumed by the service.
type Event struct {
	ID      string          `json:"id"`
	Type    string          `json:"type"`
	Payload json.RawMessage `json:"payload"`
}
