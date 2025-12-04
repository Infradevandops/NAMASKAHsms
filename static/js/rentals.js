async function loadActiveRentals() {
  const container = document.getElementById('rentals-list');
  
  try {
    const response = await fetch('/api/rentals/active');
    const rentals = await response.json();
    
    if (!rentals || rentals.length === 0) {
      container.innerHTML = '<p style="text-align: center; color: #6b7280;">No active rentals</p>';
      return;
    }

    container.innerHTML = rentals.map(rental => `
      <div class="rental-card">
        <div class="rental-info">
          <div class="rental-phone">${rental.phone_number}</div>
          <div class="rental-service">${rental.service_name} • ${rental.country_code}</div>
          <div class="rental-time">Expires: ${new Date(rental.expires_at).toLocaleString()}</div>
          <div class="rental-remaining">${formatTimeRemaining(rental.time_remaining_seconds)}</div>
        </div>
        <div class="rental-actions">
          <button onclick="viewMessages('${rental.id}')" class="btn btn-secondary">Messages</button>
          <button onclick="extendRental('${rental.id}')" class="btn btn-primary">Extend</button>
          <button onclick="releaseRental('${rental.id}')" class="btn btn-danger">Release</button>
        </div>
      </div>
    `).join('');
  } catch (error) {
    console.error('Failed to load rentals:', error);
    container.innerHTML = '<p style="text-align: center; color: #ef4444;">Error loading rentals</p>';
  }
}

function formatTimeRemaining(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${minutes}m remaining`;
}

async function extendRental(rentalId) {
  const hours = prompt('Extend by how many hours? (24, 72, 168, 720)');
  if (!hours) return;

  try {
    const response = await fetch(`/api/rentals/${rentalId}/extend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ additional_hours: parseInt(hours) })
    });

    const data = await response.json();

    if (response.status === 402) {
      alert('Insufficient credits');
      return;
    }
    if (response.status === 404) {
      alert('Rental not found');
      loadActiveRentals();
      return;
    }
    if (response.status === 410) {
      alert('Rental already expired');
      loadActiveRentals();
      return;
    }
    if (response.status === 503) {
      alert('Service temporarily unavailable');
      return;
    }
    if (!response.ok) {
      alert(`Error: ${data.detail || 'Extension failed'}`);
      return;
    }

    alert(`Extended! Cost: $${data.extension_cost.toFixed(2)}\nNew balance: $${data.remaining_credits.toFixed(2)}`);
    loadActiveRentals();
    if (window.syncBalance) window.syncBalance();
  } catch (error) {
    alert(`Network error: ${error.message}`);
  }
}

async function releaseRental(rentalId) {
  if (!confirm('Release this rental? You will receive a 50% refund.')) return;

  try {
    const response = await fetch(`/api/rentals/${rentalId}/release`, {
      method: 'POST'
    });

    const data = await response.json();

    if (response.status === 404) {
      alert('Rental not found');
      loadActiveRentals();
      return;
    }
    if (response.status === 410) {
      alert('Rental already expired');
      loadActiveRentals();
      return;
    }
    if (response.status === 503) {
      alert('Service temporarily unavailable');
      return;
    }
    if (!response.ok) {
      alert(`Error: ${data.detail || 'Release failed'}`);
      return;
    }

    alert(`Released! Refund: $${data.refund.toFixed(2)}\nNew balance: $${data.remaining_credits.toFixed(2)}`);
    loadActiveRentals();
    if (window.syncBalance) window.syncBalance();
  } catch (error) {
    alert(`Network error: ${error.message}`);
  }
}

async function viewMessages(rentalId) {
  try {
    const response = await fetch(`/api/rentals/${rentalId}/messages`);
    const data = await response.json();

    if (response.status === 404) {
      alert('Rental not found');
      return;
    }
    if (!response.ok) {
      alert(`Error: ${data.detail || 'Failed to load messages'}`);
      return;
    }
    if (data.message_count === 0) {
      alert('No messages yet');
      return;
    }

    const messages = data.messages.join('\n\n');
    alert(`Messages for ${data.phone_number}:\n\n${messages}`);
  } catch (error) {
    alert(`Network error: ${error.message}`);
  }
}

document.addEventListener('DOMContentLoaded', loadActiveRentals);
