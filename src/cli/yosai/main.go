package main

import (
	"errors"
	"fmt"
	"os"
	"os/exec"
)

const usage = "usage: yosai <build|test|deploy|logs> <service>"

func buildArgs(args []string) ([]string, error) {
	if len(args) != 2 {
		return nil, errors.New(usage)
	}
	command, service := args[0], args[1]
	switch command {
	case "build", "test", "deploy", "logs":
		return []string{"python", "-m", "tools.ops_cli", command, service}, nil
	default:
		return nil, fmt.Errorf("unknown command: %s", command)
	}
}

func main() {
	cmdArgs, err := buildArgs(os.Args[1:])
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
	cmd := exec.Command(cmdArgs[0], cmdArgs[1:]...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		fmt.Println("command failed:", err)
		os.Exit(1)
	}
}
