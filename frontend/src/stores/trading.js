import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useTradingStore = defineStore('trading', () => {
  // State
  const currentAccount = ref(null)
  const trades = ref([])
  const accounts = ref([])
  const portfolio = ref({
    totalValue: 0,
    cashBalance: 0,
    investedValue: 0,
    unrealizedPL: 0,
    realizedPL: 0,
  })

  // Computed
  const openTrades = computed(() => trades.value.filter(t => t.is_open))
  const closedTrades = computed(() => trades.value.filter(t => !t.is_open))

  const totalProfit = computed(() => {
    return closedTrades.value.reduce((sum, trade) => sum + (trade.profit_loss || 0), 0)
  })

  const winRate = computed(() => {
    if (closedTrades.value.length === 0) return 0
    const wins = closedTrades.value.filter(t => t.profit_loss > 0).length
    return (wins / closedTrades.value.length) * 100
  })

  // Actions
  const fetchAccounts = async () => {
    try {
      const response = await fetch('/api/v1/paper-trading/accounts')
      if (!response.ok) throw new Error('Failed to fetch accounts')
      accounts.value = await response.json()
    } catch (error) {
      console.error('Error fetching accounts:', error)
    }
  }

  const createAccount = async (accountData) => {
    try {
      const response = await fetch('/api/v1/paper-trading/accounts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(accountData)
      })
      if (!response.ok) throw new Error('Failed to create account')
      const newAccount = await response.json()
      accounts.value.push(newAccount)
      currentAccount.value = newAccount
      return newAccount
    } catch (error) {
      console.error('Error creating account:', error)
      throw error
    }
  }

  const setCurrentAccount = (account) => {
    currentAccount.value = account
  }

  const fetchTrades = async (accountId) => {
    try {
      const response = await fetch(`/api/v1/paper-trading/trades/${accountId}`)
      if (!response.ok) throw new Error('Failed to fetch trades')
      trades.value = await response.json()
    } catch (error) {
      console.error('Error fetching trades:', error)
    }
  }

  const createTrade = async (accountId, tradeData) => {
    try {
      const response = await fetch(`/api/v1/paper-trading/trades/${accountId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tradeData)
      })
      if (!response.ok) throw new Error('Failed to create trade')
      const newTrade = await response.json()
      trades.value.push(newTrade)
      return newTrade
    } catch (error) {
      console.error('Error creating trade:', error)
      throw error
    }
  }

  const closeTrade = async (tradeId, exitData) => {
    try {
      const response = await fetch(`/api/v1/paper-trading/trades/${tradeId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(exitData)
      })
      if (!response.ok) throw new Error('Failed to close trade')
      const closedTrade = await response.json()

      // Update trade in store
      const index = trades.value.findIndex(t => t.id === tradeId)
      if (index !== -1) {
        trades.value[index] = closedTrade
      }
      return closedTrade
    } catch (error) {
      console.error('Error closing trade:', error)
      throw error
    }
  }

  const fetchPortfolio = async (accountId) => {
    try {
      const response = await fetch(`/api/v1/paper-trading/portfolio/${accountId}`)
      if (!response.ok) throw new Error('Failed to fetch portfolio')
      const data = await response.json()
      portfolio.value = data
    } catch (error) {
      console.error('Error fetching portfolio:', error)
    }
  }

  return {
    // State
    currentAccount,
    trades,
    accounts,
    portfolio,

    // Computed
    openTrades,
    closedTrades,
    totalProfit,
    winRate,

    // Actions
    fetchAccounts,
    createAccount,
    setCurrentAccount,
    fetchTrades,
    createTrade,
    closeTrade,
    fetchPortfolio,
  }
})
