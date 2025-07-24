const express = require('express');
const { ApolloServer, gql } = require('apollo-server-express');
const { createServer } = require('http');
const { WebSocketServer } = require('ws');
const { useServer } = require('graphql-ws/lib/use/ws');
const axios = require('axios');
const DataLoader = require('dataloader');
const { PubSub } = require('graphql-subscriptions');
const depthLimit = require('graphql-depth-limit');

const REST_BASE = process.env.REST_BASE || 'http://localhost:5001';
const pubsub = new PubSub();
const ANALYTICS_UPDATED = 'ANALYTICS_UPDATED';

// Simple schema for analytics summary
const typeDefs = gql`
  type AnalyticsSummary {
    total_records: Int
    unique_users: Int
    unique_devices: Int
  }

  type Query {
    analyticsSummary(facilityId: String, range: String): AnalyticsSummary
  }

  type Subscription {
    analyticsUpdated: AnalyticsSummary
  }
`;

const analyticsLoader = new DataLoader(async keys => {
  return Promise.all(
    keys.map(async ({ facilityId, range }) => {
      const resp = await axios.get(`${REST_BASE}/api/v1/analytics/patterns`, {
        params: { facility_id: facilityId, range }
      });
      const data = resp.data;
      return {
        total_records: data.data_summary?.total_records,
        unique_users: data.data_summary?.unique_users,
        unique_devices: data.data_summary?.unique_devices,
      };
    })
  );
});

const resolvers = {
  Query: {
    analyticsSummary: (_, args) => {
      const facilityId = args.facilityId || 'default';
      const range = args.range || '30d';
      return analyticsLoader.load({ facilityId, range });
    },
  },
  Subscription: {
    analyticsUpdated: {
      subscribe: () => pubsub.asyncIterator([ANALYTICS_UPDATED])
    }
  }
};

async function start() {
  const app = express();
  const httpServer = createServer(app);

  const server = new ApolloServer({
    typeDefs,
    resolvers,
    context: ({ req }) => ({ token: req.headers.authorization }),
    validationRules: [depthLimit(5)]
  });
  await server.start();
  server.applyMiddleware({ app, path: '/graphql' });

  const wsServer = new WebSocketServer({ server: httpServer, path: '/graphql' });
  useServer({ schema: server.schema, context: () => ({}) }, wsServer);

  const PORT = process.env.GRAPHQL_PORT || 4000;
  httpServer.listen(PORT, () => {
    console.log(`GraphQL server ready at http://localhost:${PORT}${server.graphqlPath}`);
  });
}

start();
