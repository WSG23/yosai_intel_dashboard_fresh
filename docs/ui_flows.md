# UI Flows

This document illustrates the key interactions that users perform in the dashboard UI.
The focus is on the upload, analytics and export steps that most users follow.

## Upload a File

```mermaid
sequenceDiagram
    participant U as User
    participant B as Browser
    participant S as Server
    participant AS as AnalyticsService

    U->>B: Drag or select file
    B->>S: POST /api/v1/upload
    S->>AS: validate_and_store()
    AS-->>S: confirmation
    S-->>B: Show upload success
```

## Run Analytics

```mermaid
flowchart TD
    A[File Uploaded] --> B[Run analytics]
    B --> C[Display charts]
```

## Export Results

```mermaid
sequenceDiagram
    participant U as User
    participant B as Browser
    participant S as Server
    participant DB as Database

    U->>B: Click Export
    B->>S: GET /export
    S->>DB: Fetch results
    DB-->>S: Data
    S-->>B: Download file
```
