package errors

import (
	"fmt"
	"log"
)

// Errorf formats according to a format specifier and logs the
// resulting error before returning it.
func Errorf(format string, args ...any) error {
	err := fmt.Errorf(format, args...)
	log.Printf("%v", err)
	return err
}

// Wrap annotates err with msg and logs the wrapped error.
// It returns nil if err is nil.
func Wrap(err error, msg string) error {
	if err == nil {
		return nil
	}
	return Errorf("%s: %w", msg, err)
}
