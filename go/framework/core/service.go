package core

// Service represents a runnable service with start and stop lifecycle methods.
type Service interface {
	Start()
	Stop()
}
