/**
 * State Manager Tests
 */

import { stateManager } from '../modules/state.js';

describe('StateManager', () => {
  beforeEach(() => {
    stateManager.state = {
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
    stateManager.listeners = [];
  });

  describe('setState', () => {
    test('should update state', () => {
      stateManager.setState({ balance: 100 });
      expect(stateManager.state.balance).toBe(100);
    });

    test('should merge nested objects', () => {
      stateManager.setState({
        verification: { areaCode: '201' }
      });
      expect(stateManager.state.verification.areaCode).toBe('201');
      expect(stateManager.state.verification.step).toBe(1);
    });

    test('should notify listeners', () => {
      const listener = jest.fn();
      stateManager.subscribe(listener);
      stateManager.setState({ balance: 50 });
      expect(listener).toHaveBeenCalledWith(stateManager.state);
    });
  });

  describe('subscribe', () => {
    test('should add listener', () => {
      const listener = jest.fn();
      stateManager.subscribe(listener);
      expect(stateManager.listeners.length).toBe(1);
    });

    test('should call listener on state change', () => {
      const listener = jest.fn();
      stateManager.subscribe(listener);
      stateManager.setState({ balance: 75 });
      expect(listener).toHaveBeenCalled();
    });
  });

  describe('unsubscribe', () => {
    test('should remove listener', () => {
      const listener = jest.fn();
      stateManager.subscribe(listener);
      stateManager.unsubscribe(listener);
      expect(stateManager.listeners.length).toBe(0);
    });
  });

  describe('getState', () => {
    test('should return current state', () => {
      const state = stateManager.getState();
      expect(state.balance).toBe(0);
      expect(state.currentView).toBe('home');
    });
  });
});
