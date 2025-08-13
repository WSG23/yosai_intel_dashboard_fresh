# SDK Integration Guide

## TypeScript

Install the client:

```bash
npm install ./sdks/typescript
```

Usage:

```ts
import { DefaultApi, Configuration } from './sdks/typescript';

const api = new DefaultApi(new Configuration({
  basePath: 'https://api.yosai.com/v1',
  accessToken: 'TOKEN',
}));

const flags = await api.listFeatureFlags();
console.log(flags);
```

## Go

Install the client:

```bash
go get ./sdks/go
```

Usage:

```go
package main

import (
  "context"
  yd "./sdks/go"
)

func main() {
  cfg := yd.NewConfiguration()
  cfg.Servers = yd.ServerConfigurations{{URL: "https://api.yosai.com/v1"}}
  client := yd.NewAPIClient(cfg)
  flags, _, err := client.DefaultAPI.ListFeatureFlags(context.Background()).Execute()
  _ = err
  _ = flags
}
```
