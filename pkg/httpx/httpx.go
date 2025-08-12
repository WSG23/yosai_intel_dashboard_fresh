package httpx

import (
    "context"
    "encoding/json"
    "net/http"
    "time"
)

// DefaultClient is the client used by DoJSON. It has a
// non-zero timeout to avoid hanging requests.
var DefaultClient = &http.Client{Timeout: 10 * time.Second}

// DoJSON executes the HTTP request using DefaultClient and decodes
// the JSON response body into dst. The provided context controls the
// request and will cancel the call if it is done.
func DoJSON(ctx context.Context, req *http.Request, dst any) error {
    req = req.WithContext(ctx)
    resp, err := DefaultClient.Do(req)
    if err != nil {
        return err
    }
    defer resp.Body.Close()
    return json.NewDecoder(resp.Body).Decode(dst)
}

