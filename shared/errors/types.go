package errors

type Error interface {
	error
	Code() string
}

type BaseError struct {
	Msg     string
	CodeStr string
}

func (e BaseError) Error() string { return e.Msg }
func (e BaseError) Code() string  { return e.CodeStr }

var (
	ErrConfig = BaseError{Msg: "configuration error", CodeStr: "CONFIG_ERROR"}
)
