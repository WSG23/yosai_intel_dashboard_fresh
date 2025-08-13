# Go Error Handling

The `pkg/errors` package provides helpers for consistent error wrapping and logging.

## Wrapping an Existing Error

```go
package main

import (
    "os"

    xerrors "github.com/WSG23/errors"
)

func loadConfig(path string) error {
    data, err := os.ReadFile(path)
    if err != nil {
        return xerrors.Wrap(err, "read config")
    }
    _ = data
    return nil
}
```

## Creating a New Error

```go
return xerrors.Errorf("invalid user input: %s", value)
```

Both helpers automatically log the generated error.
