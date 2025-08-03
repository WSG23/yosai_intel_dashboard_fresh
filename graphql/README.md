# GraphQL Service

This folder contains a lightweight GraphQL layer for the Yosai Intel Dashboard.

`index.js` starts an Apollo Server instance backed by the existing REST API. It
defines a basic schema for analytics data, resolves queries via `axios` calls to
the REST endpoints and exposes a subscription example. `DataLoader` is used to
batch and cache requests when the same analytics data is requested multiple
times during a single GraphQL operation, ensuring each facility/time range pair
is fetched only once. Query depth is limited to prevent expensive queries.

Run the server locally with:

```bash
npm run graphql
```

The server listens on port `4000` by default and expects the REST API to be
available at `http://localhost:5001`. Set the `REST_BASE` environment variable to
change the target API host.
