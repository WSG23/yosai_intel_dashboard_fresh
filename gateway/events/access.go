package events

import (
	"errors"
	"time"
)

type AccessEvent struct {
	EventID           string    `json:"event_id"`
	Timestamp         time.Time `json:"timestamp"`
	PersonID          string    `json:"person_id"`
	DoorID            string    `json:"door_id"`
	BadgeID           string    `json:"badge_id,omitempty"`
	AccessResult      string    `json:"access_result"`
	BadgeStatus       string    `json:"badge_status,omitempty"`
	DoorHeldOpenTime  float64   `json:"door_held_open_time,omitempty"`
	EntryWithoutBadge bool      `json:"entry_without_badge,omitempty"`
	DeviceStatus      string    `json:"device_status,omitempty"`
	ProcessedAt       time.Time `json:"processed_at,omitempty"`
}

func (e AccessEvent) Validate() error {
	if e.EventID == "" || e.PersonID == "" || e.DoorID == "" || e.AccessResult == "" {
		return errors.New("missing required fields")
	}
	if e.Timestamp.IsZero() {
		return errors.New("missing timestamp")
	}
	return nil
}
