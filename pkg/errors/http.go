package errors

import (
    "encoding/json"
    "net/http"
)

// Code represents a standardized error code shared across services.
type Code string

const (
    InvalidInput Code = "invalid_input"
    Unauthorized Code = "unauthorized"
    NotFound     Code = "not_found"
    Internal     Code = "internal"
    Unavailable  Code = "unavailable"
)

// Error is the standardized error response payload.
type Error struct {
    Code    Code        `json:"code"`
    Message string      `json:"message"`
    Details interface{} `json:"details"`
}

// WriteJSON writes the error as JSON to the http.ResponseWriter.
func WriteJSON(w http.ResponseWriter, status int, code Code, message string, details interface{}) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(status)
    _ = json.NewEncoder(w).Encode(Error{Code: code, Message: message, Details: details})
}

