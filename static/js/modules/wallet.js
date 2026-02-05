// Wallet Module
import axios from 'axios'

export function initWallet() {
  const addCreditsBtn = document.getElementById('add-credits-btn')
  const withdrawBtn = document.getElementById('withdraw-btn')

  if (addCreditsBtn) addCreditsBtn.addEventListener('click', showAddCreditsModal)
  if (withdrawBtn) withdrawBtn.addEventListener('click', showWithdrawModal)

  loadWalletBalance()
}

async function loadWalletBalance() {
  try {
    const response = await axios.get('/api/wallet/balance')
    const balanceEl = document.getElementById('wallet-balance')
    if (balanceEl) balanceEl.textContent = '$' + response.data.balance.toFixed(2)
  } catch (error) {
    console.error('Failed to load wallet balance:', error)
  }
}

function showAddCreditsModal() {
  const modal = document.getElementById('add-credits-modal')
  if (modal) modal.style.display = 'block'
}

function showWithdrawModal() {
  const modal = document.getElementById('withdraw-modal')
  if (modal) modal.style.display = 'block'
}

async function addCredits(amount) {
  try {
    await axios.post('/api/wallet/add-credits', { amount })
    alert('Credits added successfully!')
    loadWalletBalance()
  } catch (error) {
    alert('Failed to add credits: ' + (error.response?.data?.detail || 'Unknown error'))
  }
}

async function withdraw(amount) {
  try {
    await axios.post('/api/wallet/withdraw', { amount })
    alert('Withdrawal initiated!')
    loadWalletBalance()
  } catch (error) {
    alert('Failed to withdraw: ' + (error.response?.data?.detail || 'Unknown error'))
  }
}

export { loadWalletBalance, showAddCreditsModal, showWithdrawModal, addCredits, withdraw }
