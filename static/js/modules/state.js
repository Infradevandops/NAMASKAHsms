/**
 * State Management Module
 * Single source of truth for application state
 */

class StateManager {
  constructor() {
    this.state = {
      user: null,
      balance: 0,
      currentView: 'home',
      verification: {
        step: 1,
        areaCode: null,
        service: null,
        carrier: null,
        cost: 0,
        verificationId: null,
        pollingInterval: null,
        areaCodes: [],
        services: [],
        carriers: []
      }
    };
    this.listeners = [];
  }

  /**
   * Update state with new values
   * @param {Object} updates - Partial state updates
   * @returns {void}
   */
  setState(updates) {
    this.state = { ...this.state, ...updates };
    this.notify();
  }

  /**
   * Subscribe to state changes
   * @param {Function} listener - Callback function
   * @returns {void}
   */
  subscribe(listener) {
    this.listeners.push(listener);
  }

  /**
   * Unsubscribe from state changes
   * @param {Function} listener - Callback function
   * @returns {void}
   */
  unsubscribe(listener) {
    this.listeners = this.listeners.filter(l => l !== listener);
  }

  /**
   * Notify all listeners of state change
   * @returns {void}
   */
  notify() {
    this.listeners.forEach(listener => listener(this.state));
  }

  /**
   * Get current state
   * @returns {Object} Current state
   */
  getState() {
    return this.state;
  }
}

export const stateManager = new StateManager();
