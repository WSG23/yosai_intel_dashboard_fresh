package httpx

import (
	"encoding/json"
	"errors"
	"io"
)

// DecodeJSON decodes JSON from r into dst and ensures the entire
// input is consumed. If additional tokens remain after the JSON value,
// an error is returned.
func DecodeJSON(r io.Reader, dst any) error {
	dec := json.NewDecoder(r)
	if err := dec.Decode(dst); err != nil {
		return err
	}
	// Ensure the decoder has reached EOF to avoid accepting trailing data.
	if _, err := dec.Token(); err != io.EOF {
		if err == nil {
			err = errors.New("unexpected data after JSON value")
		}
		return err
	}
	return nil
}
