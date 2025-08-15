package framework

import (
	"net/http"

        sharederrors "github.com/WSG23/errors"
)

type ServiceError = sharederrors.Error

var DefaultCodeToStatus = map[sharederrors.Code]int{
	sharederrors.InvalidInput: http.StatusBadRequest,
	sharederrors.Unauthorized: http.StatusUnauthorized,
	sharederrors.NotFound:     http.StatusNotFound,
	sharederrors.Internal:     http.StatusInternalServerError,
	sharederrors.Unavailable:  http.StatusServiceUnavailable,
}

type ErrorHandler struct {
	Mapping map[sharederrors.Code]int
}

func NewErrorHandler() *ErrorHandler {
	return &ErrorHandler{Mapping: DefaultCodeToStatus}
}

func (h *ErrorHandler) Handle(w http.ResponseWriter, err ServiceError) {
	status, ok := h.Mapping[err.Code]
	if !ok {
		status = http.StatusInternalServerError
	}
	sharederrors.WriteJSON(w, status, err.Code, err.Message, err.Details)
}
