/**
 * Binance WebSocket Service
 * Handles real-time market data streams
 */

const BINANCE_WS_URL = 'wss://stream.binance.com:9443/ws'

class BinanceWebSocket {
  constructor() {
    this.ws = null
    this.subscriptions = new Map() // streamName -> callbacks
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 3000
    this.isIntentionallyClosed = false
    this.messageQueue = []
    this.isConnected = false
    this.connectPromise = null // Guard against concurrent connects
  }

  /**
   * Connect to Binance WebSocket
   */
  connect() {
    // If already connected, return immediately
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return Promise.resolve()
    }

    // If connection attempt is already in progress, return that promise
    if (this.connectPromise) {
      return this.connectPromise
    }

    // Create new connection promise
    this.connectPromise = new Promise((resolve, reject) => {
      try {
        console.log('Connecting to Binance WebSocket...')
        this.isConnected = false // Reset flag before creating new connection
        this.ws = new WebSocket(BINANCE_WS_URL)

        this.ws.onopen = () => {
          console.log('WebSocket connected')
          this.isConnected = true
          this.reconnectAttempts = 0
          this.isIntentionallyClosed = false

          // Process queued subscriptions
          this.processQueue()
          this.connectPromise = null
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            this.handleMessage(data)
          } catch (err) {
            console.error('Error parsing WebSocket message:', err)
          }
        }

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          this.isConnected = false
          this.connectPromise = null
          reject(error)
        }

        this.ws.onclose = () => {
          console.log('WebSocket closed')
          this.isConnected = false
          if (!this.isIntentionallyClosed) {
            this.reconnect()
          }
        }
      } catch (err) {
        console.error('Failed to create WebSocket:', err)
        this.connectPromise = null
        reject(err)
      }
    })

    return this.connectPromise
  }

  /**
   * Reconnect with exponential backoff
   */
  reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`)

    setTimeout(() => {
      this.connect().catch(() => {
        // Will retry again
      })
    }, delay)
  }

  /**
   * Subscribe to a stream
   * @param {string} symbol - Trading pair (e.g., 'BTCUSDT')
   * @param {string} streamType - Type of stream (klines, ticker)
   * @param {string} interval - Interval for klines (1m, 5m, 1h, etc.)
   * @param {function} callback - Function to call when data arrives
   */
  subscribe(symbol, streamType, interval, callback) {
    // Normalize interval to lowercase
    const normalizedInterval = interval ? interval.toLowerCase() : null
    const streamName = normalizedInterval
      ? `${symbol.toLowerCase()}@${streamType}_${normalizedInterval}`
      : `${symbol.toLowerCase()}@${streamType}`

    // Store callback
    if (!this.subscriptions.has(streamName)) {
      this.subscriptions.set(streamName, [])
    }
    this.subscriptions.get(streamName).push(callback)

    // Send subscription only if connection is OPEN
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.sendSubscribe(streamName)
    } else {
      this.messageQueue.push({ action: 'subscribe', streams: [streamName] })
    }

    // Return unsubscribe function
    return () => this.unsubscribe(streamName, callback)
  }

  /**
   * Unsubscribe from a stream
   */
  unsubscribe(streamName, callback) {
    const callbacks = this.subscriptions.get(streamName)
    if (callbacks) {
      const index = callbacks.indexOf(callback)
      if (index > -1) {
        callbacks.splice(index, 1)
      }

      // If no more callbacks, remove stream entirely
      if (callbacks.length === 0) {
        this.subscriptions.delete(streamName)
        if (this.isConnected && this.ws) {
          this.sendUnsubscribe(streamName)
        }
      }
    }
  }

  /**
   * Send subscription message to WebSocket
   */
  sendSubscribe(streamName) {
    const message = {
      method: 'SUBSCRIBE',
      params: [streamName],
      id: Date.now()
    }
    this.send(message)
  }

  /**
   * Send unsubscription message to WebSocket
   */
  sendUnsubscribe(streamName) {
    const message = {
      method: 'UNSUBSCRIBE',
      params: [streamName],
      id: Date.now()
    }
    this.send(message)
  }

  /**
   * Send raw message
   */
  send(message) {
    if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    }
  }

  /**
   * Process queued messages after reconnection
   */
  processQueue() {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift()
      this.send(message)
    }

    // Re-subscribe to all active streams
    for (const streamName of this.subscriptions.keys()) {
      this.sendSubscribe(streamName)
    }
  }

  /**
   * Handle incoming WebSocket message
   */
  handleMessage(data) {
    // Subscription confirmation - ignore
    if (data.result !== undefined) {
      return
    }

    // Klines (candlestick) data
    if (data.k) {
      const streamName = `${data.s.toLowerCase()}@klines_${data.k.i}`
      const callbacks = this.subscriptions.get(streamName)
      if (callbacks) {
        const candleData = {
          time: Math.floor(data.k.t / 1000), // Convert ms to seconds
          open: parseFloat(data.k.o),
          high: parseFloat(data.k.h),
          low: parseFloat(data.k.l),
          close: parseFloat(data.k.c),
          volume: parseFloat(data.k.v),
          isClosed: data.k.x // true when candle is closed
        }
        callbacks.forEach(cb => cb(candleData, data.s))
      }
    }

    // Aggregate Trade data
    if (data.a !== undefined) {
      const streamName = `${data.s.toLowerCase()}@aggTrade`
      const callbacks = this.subscriptions.get(streamName)
      if (callbacks) {
        const tradeData = {
          id: data.a,
          time: data.T,
          price: data.p,
          qty: data.q,
          symbol: data.s
        }
        callbacks.forEach(cb => cb(tradeData))
      }
    }

    // Ticker data (24h stats)
    if (data.c && data.s && data.e === '24hrTicker') {
      // Check if this is a ticker message by looking for expected ticker fields
      const streamName = `${data.s.toLowerCase()}@ticker`
      const callbacks = this.subscriptions.get(streamName)
      if (callbacks) {
        const tickerData = {
          symbol: data.s,
          price: parseFloat(data.c),
          price_change: parseFloat(data.p),
          price_change_percent: parseFloat(data.P),
          high: parseFloat(data.h),
          low: parseFloat(data.l),
          volume: parseFloat(data.v),
          quote_volume: parseFloat(data.q)
        }
        callbacks.forEach(cb => cb(tickerData))
      }
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnect() {
    this.isIntentionallyClosed = true
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.subscriptions.clear()
    this.messageQueue = []
  }

  /**
   * Get connection status
   */
  getStatus() {
    return {
      connected: this.isConnected,
      subscriptions: this.subscriptions.size,
      reconnectAttempts: this.reconnectAttempts
    }
  }
}

// Singleton instance
export const binanceWS = new BinanceWebSocket()

export default binanceWS
