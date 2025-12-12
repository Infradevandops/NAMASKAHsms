/**
 * Event Bus Module
 * Loose coupling between components
 */

export const events = {
  AREA_CODE_CHANGED: 'areaCodeChanged',
  SERVICE_CHANGED: 'serviceChanged',
  CARRIER_CHANGED: 'carrierChanged',
  VERIFICATION_STARTED: 'verificationStarted',
  VERIFICATION_COMPLETED: 'verificationCompleted',
  ERROR_OCCURRED: 'errorOccurred'
};

export class EventBus {
  constructor() {
    this.listeners = new Map();
  }

  /**
   * Subscribe to event
   * @param {string} event - Event name
   * @param {Function} callback - Callback function
   * @returns {void}
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  /**
   * Emit event
   * @param {string} event - Event name
   * @param {*} data - Event data
   * @returns {void}
   */
  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => callback(data));
    }
  }

  /**
   * Unsubscribe from event
   * @param {string} event - Event name
   * @param {Function} callback - Callback function
   * @returns {void}
   */
  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) callbacks.splice(index, 1);
    }
  }
}

export const eventBus = new EventBus();
