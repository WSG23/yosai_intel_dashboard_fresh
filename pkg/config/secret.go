package config

import (
	"io/ioutil"
	"sync"

	"github.com/fsnotify/fsnotify"
)

// SecretWatcher watches a file and reloads its contents when updated.
type SecretWatcher struct {
	Path  string
	mu    sync.RWMutex
	value string
}

// NewSecretWatcher creates a watcher for the given file path.
func NewSecretWatcher(path string) (*SecretWatcher, error) {
	w := &SecretWatcher{Path: path}
	if err := w.reload(); err != nil {
		return nil, err
	}

	watcher, err := fsnotify.NewWatcher()
	if err != nil {
		return nil, err
	}
	if err := watcher.Add(path); err != nil {
		watcher.Close()
		return nil, err
	}

	go func() {
		for range watcher.Events {
			w.reload()
		}
	}()

	return w, nil
}

// Value returns the latest secret value.
func (w *SecretWatcher) Value() string {
	w.mu.RLock()
	defer w.mu.RUnlock()
	return w.value
}

func (w *SecretWatcher) reload() error {
	data, err := ioutil.ReadFile(w.Path)
	if err != nil {
		return err
	}
	w.mu.Lock()
	w.value = string(data)
	w.mu.Unlock()
	return nil
}
