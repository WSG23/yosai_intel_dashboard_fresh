# Progressive Web App Strategy

This project uses a Workbox-driven service worker to deliver offline support
and reliable caching for core assets and API data.

## Cache Versioning

Caches are versioned via the `CACHE_VERSION` constant inside
`public/service-worker.js`. Incrementing this value creates new cache names for
runtime data and static assets. When the service worker activates, Workbox
manages old caches and the newly versioned caches take effect, ensuring stale
resources are removed on update.

## Updating the Service Worker

1. Bump the `CACHE_VERSION` constant when core assets change or cache
   strategies are modified.
2. Deploy the updated service worker along with the new assets.
3. Clients will fetch the new service worker, install it, and activate the new
   caches on the next load. Previously cached resources are purged as part of
   the activation step.

This approach provides predictable cache invalidation and guarantees users see
fresh content after each release while still benefiting from offline access.
