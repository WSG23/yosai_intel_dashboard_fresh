# Build stage
FROM golang:1.23@sha256:48701ce865534290020481ccb9a78f3b3e46352ba6f1270d987da9cccc591ce8 AS build
WORKDIR /src
COPY go ./go
COPY resilience ./resilience
COPY services/event_processing ./services/event_processing
WORKDIR /src/services/event_processing
RUN go build -o processor ./cmd/processor

# Runtime stage
FROM gcr.io/distroless/base-debian12@sha256:4f6e739881403e7d50f52a4e574c4e3c88266031fd555303ee2f1ba262523d6a
COPY --from=build /src/services/event_processing/processor /usr/local/bin/processor
USER 1000
ENTRYPOINT ["/usr/local/bin/processor"]
