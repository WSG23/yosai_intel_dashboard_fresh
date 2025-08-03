import { eventBus } from '../eventBus';

let websocket_connections_total = 0;
let websocket_reconnect_attempts_total = 0;
let websocket_ping_failures_total = 0;

export const snapshot = () => ({
  websocket_connections_total,
  websocket_reconnect_attempts_total,
  websocket_ping_failures_total,
});

const publish = () => {
  eventBus.emit('metrics_update', snapshot());
};

export const record_connection = () => {
  websocket_connections_total += 1;
  publish();
};

export const record_reconnect_attempt = () => {
  websocket_reconnect_attempts_total += 1;
  publish();
};

export const record_ping_failure = () => {
  websocket_ping_failures_total += 1;
  publish();
};

export const reset = () => {
  websocket_connections_total = 0;
  websocket_reconnect_attempts_total = 0;
  websocket_ping_failures_total = 0;
};

export const publish_snapshot = publish;

const websocket_metrics = {
  record_connection,
  record_reconnect_attempt,
  record_ping_failure,
  snapshot,
  publish_snapshot,
  reset,
};

export default websocket_metrics;
