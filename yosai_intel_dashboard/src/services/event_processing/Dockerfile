# Build stage
FROM golang:1.23 AS build
WORKDIR /src
COPY go ./go
COPY resilience ./resilience
COPY services/event_processing ./services/event_processing
WORKDIR /src/services/event_processing
RUN go build -o processor ./cmd/processor

# Runtime stage
FROM gcr.io/distroless/base-debian12
COPY --from=build /src/services/event_processing/processor /usr/local/bin/processor
ENTRYPOINT ["/usr/local/bin/processor"]
