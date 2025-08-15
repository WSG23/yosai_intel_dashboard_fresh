package main

import (
	"reflect"
	"testing"
)

func TestBuildArgsValid(t *testing.T) {
	args, err := buildArgs([]string{"build", "gateway"})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	expect := []string{"python", "-m", "tools.ops_cli", "build", "gateway"}
	if !reflect.DeepEqual(args, expect) {
		t.Fatalf("expected %v, got %v", expect, args)
	}
}

func TestBuildArgsUnknown(t *testing.T) {
	if _, err := buildArgs([]string{"foo", "svc"}); err == nil {
		t.Fatalf("expected error")
	}
}

func TestBuildArgsMissing(t *testing.T) {
	if _, err := buildArgs([]string{"build"}); err == nil {
		t.Fatalf("expected error")
	}
}

func TestBuildArgsLogs(t *testing.T) {
	args, err := buildArgs([]string{"logs", "gateway"})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	expect := []string{"python", "-m", "tools.ops_cli", "logs", "gateway"}
	if !reflect.DeepEqual(args, expect) {
		t.Fatalf("expected %v, got %v", expect, args)
	}
}
