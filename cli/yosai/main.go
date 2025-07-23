package main

import (
	"fmt"
	"os"
	"os/exec"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Println("usage: yosai <build|test|deploy|logs>")
		os.Exit(1)
	}
	var cmd *exec.Cmd
	switch os.Args[1] {
	case "build":
		cmd = exec.Command("make", "build")
	case "test":
		cmd = exec.Command("make", "test")
	case "deploy":
		cmd = exec.Command("make", "deploy")
	case "logs":
		cmd = exec.Command("make", "logs")
	default:
		fmt.Println("unknown command")
		os.Exit(1)
	}
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		fmt.Println("command failed:", err)
		os.Exit(1)
	}
}
