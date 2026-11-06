/**
 * Kant Compiler Toolchain - Server-Sent Events (SSE) Client
 * Robust connection manager with exponential backoff and event multiplexing.
 */

export class SSEClient {
  constructor(endpoint = '/api/events', options = {}) {
    this.endpoint = endpoint;
    this.options = Object.assign({
      initialDelayMs: 1000,
      maxDelayMs: 30000,
      backoffFactor: 2,
      maxReconnectAttempts: Infinity,
    }, options);

    this.eventSource = null;
    this.reconnectAttempts = 0;
    this.currentDelayMs = this.options.initialDelayMs;
    this.reconnectTimer = null;
    this.status = 'disconnected'; // 'connecting' | 'connected' | 'reconnecting' | 'disconnected'
    this.listeners = new Map(); // eventName -> Set(callbacks)
  }

  on(eventName, callback) {
    if (!this.listeners.has(eventName)) {
      this.listeners.set(eventName, new Set());
    }
    this.listeners.get(eventName).add(callback);
    return () => this.off(eventName, callback);
  }

  off(eventName, callback) {
    if (this.listeners.has(eventName)) {
      this.listeners.get(eventName).delete(callback);
    }
  }

  emit(eventName, data) {
    if (this.listeners.has(eventName)) {
      for (const cb of this.listeners.get(eventName)) {
        try {
          cb(data);
        } catch (err) {
          console.error(`SSEClient listener error for '${eventName}':`, err);
        }
      }
    }
  }

  setStatus(newStatus) {
    if (this.status !== newStatus) {
      this.status = newStatus;
      this.emit('status_change', { status: newStatus, attempts: this.reconnectAttempts });
    }
  }

  getStatus() {
    return this.status;
  }

  connect() {
    if (typeof EventSource === 'undefined') {
      console.warn('EventSource is not supported in this runtime environment.');
      this.setStatus('disconnected');
      return;
    }

    if (this.eventSource) {
      this.disconnect();
    }

    this.setStatus(this.reconnectAttempts > 0 ? 'reconnecting' : 'connecting');

    try {
      this.eventSource = new EventSource(this.endpoint);

      this.eventSource.onopen = () => {
        this.reconnectAttempts = 0;
        this.currentDelayMs = this.options.initialDelayMs;
        this.setStatus('connected');
        this.emit('connected', { timestamp: new Date().toISOString() });
      };

      this.eventSource.onmessage = (e) => {
        try {
          const payload = JSON.parse(e.data);
          this.emit('message', payload);
          if (payload.type) {
            this.emit(payload.type, payload.data || payload);
          }
        } catch (err) {
          this.emit('raw_message', e.data);
        }
      };

      // Custom SSE event types
      this.eventSource.addEventListener('state_update', (e) => {
        try {
          const data = JSON.parse(e.data);
          this.emit('state_update', data);
        } catch (err) {
          console.error('Failed to parse state_update event:', err);
        }
      });

      this.eventSource.addEventListener('telemetry_event', (e) => {
        try {
          const data = JSON.parse(e.data);
          this.emit('telemetry_event', data);
        } catch (err) {
          console.error('Failed to parse telemetry_event event:', err);
        }
      });

      this.eventSource.addEventListener('ping', (e) => {
        this.emit('ping', { timestamp: new Date().toISOString() });
      });

      this.eventSource.onerror = (err) => {
        this.eventSource.close();
        this.eventSource = null;
        this.setStatus('disconnected');
        this.scheduleReconnect();
      };
    } catch (err) {
      console.error('SSE connection instantiation failed:', err);
      this.setStatus('disconnected');
      this.scheduleReconnect();
    }
  }

  scheduleReconnect() {
    if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      console.warn('SSE max reconnection attempts reached.');
      return;
    }

    this.reconnectAttempts += 1;
    this.setStatus('reconnecting');

    const jitter = Math.random() * 500;
    const delay = Math.min(this.currentDelayMs + jitter, this.options.maxDelayMs);

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    this.reconnectTimer = setTimeout(() => {
      this.currentDelayMs = Math.min(this.currentDelayMs * this.options.backoffFactor, this.options.maxDelayMs);
      this.connect();
    }, delay);
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    this.setStatus('disconnected');
  }
}
