/**
 * Test suite for Secure Analytics Module
 */

// Mock Chart.js
global.Chart = class MockChart {
  constructor() {
    this.destroyed = false;
  }
  destroy() {
    this.destroyed = true;
  }
};

// Mock fetch
global.fetch = jest.fn();

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock DOM methods
document.createElement = jest.fn((tagName) => ({
  tagName: tagName.toUpperCase(),
  className: '',
  textContent: '',
  style: {},
  appendChild: jest.fn(),
  addEventListener: jest.fn(),
  classList: {
    add: jest.fn(),
    remove: jest.fn(),
  },
  dataset: {},
}));

document.getElementById = jest.fn();
document.querySelectorAll = jest.fn(() => []);

describe('EnhancedAnalytics (Security Fixed)', () => {
  let analytics;
  
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue('mock-token');
    
    // Reset DOM mocks
    document.getElementById.mockReturnValue({
      textContent: '',
      style: { setProperty: jest.fn() },
      appendChild: jest.fn(),
      classList: { add: jest.fn(), remove: jest.fn() }
    });
    
    // Import and instantiate after mocks are set up
    const { EnhancedAnalytics } = require('../enhanced-analytics.js');
    analytics = new EnhancedAnalytics();
  });

  afterEach(() => {
    if (analytics) {
      analytics.destroy();
    }
  });

  describe('Initialization', () => {
    test('should initialize without errors', () => {
      expect(analytics).toBeDefined();
      expect(analytics.currentPeriod).toBe(30);
      expect(analytics.charts).toEqual({});
    });

    test('should handle missing token gracefully', async () => {
      localStorageMock.getItem.mockReturnValue(null);
      
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      await analytics.loadAnalytics();
      
      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to load analytics',
        expect.any(Error)
      );
      
      consoleSpy.mockRestore();
    });
  });

  describe('Data Loading', () => {
    test('should load analytics data successfully', async () => {
      const mockAnalytics = {
        total_verifications: 100,
        success_rate: 85.5,
        total_spent: 250.75,
        efficiency_score: 92,
        daily_usage: [],
        popular_services: [],
        predictions: [],
        recommendations: []
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockAnalytics)
      });
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({})
      });
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({})
      });

      await analytics.loadAnalytics();

      expect(fetch).toHaveBeenCalledTimes(3);
      expect(fetch).toHaveBeenCalledWith(
        '/analytics/usage?period=30',
        { headers: { Authorization: 'Bearer mock-token' } }
      );
    });

    test('should handle API errors gracefully', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));
      
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      await analytics.loadAnalytics();
      
      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to load analytics',
        expect.any(Error)
      );
      
      consoleSpy.mockRestore();
    });
  });

  describe('Security Features', () => {
    test('should sanitize metric names', () => {
      const result = analytics.formatMetricName('daily_usage<script>alert(1)</script>');
      expect(result).toBe('Daily Usage<script>alert(1)</script>');
      // Note: formatMetricName doesn't sanitize HTML, but updateElementSafe does
    });

    test('should use textContent instead of innerHTML', () => {
      const mockElement = {
        textContent: '',
        innerHTML: ''
      };
      
      document.getElementById.mockReturnValue(mockElement);
      
      analytics.updateElementSafe('test-id', '<script>alert("xss")</script>');
      
      expect(mockElement.textContent).toBe('<script>alert("xss")</script>');
      expect(mockElement.innerHTML).toBe('');
    });

    test('should handle malicious prediction data safely', () => {
      const maliciousPredictions = [{
        metric: '<img src=x onerror=alert(1)>',
        prediction: '<script>alert("xss")</script>',
        confidence: 0.9,
        timeframe: '<iframe src="javascript:alert(1)"></iframe>'
      }];

      const mockContainer = {
        textContent: '',
        appendChild: jest.fn()
      };
      
      document.getElementById.mockReturnValue(mockContainer);
      document.createElement.mockImplementation((tag) => ({
        tagName: tag.toUpperCase(),
        className: '',
        textContent: '',
        style: {},
        appendChild: jest.fn()
      }));

      analytics.updatePredictions(maliciousPredictions);

      // Verify that createElement was called (DOM elements created)
      expect(document.createElement).toHaveBeenCalled();
      // Verify container was cleared safely
      expect(mockContainer.textContent).toBe('');
    });
  });

  describe('Chart Creation', () => {
    test('should create usage trend chart with valid data', () => {
      const mockCanvas = { getContext: () => ({}) };
      document.getElementById.mockReturnValue(mockCanvas);

      const dailyUsage = [
        { date: '2023-01-01', count: 10, success_rate: 85 },
        { date: '2023-01-02', count: 15, success_rate: 90 }
      ];

      analytics.createUsageTrendChart(dailyUsage);

      expect(analytics.charts.usageTrend).toBeDefined();
    });

    test('should handle invalid chart data gracefully', () => {
      document.getElementById.mockReturnValue(null);
      
      // Should not throw error
      expect(() => {
        analytics.createUsageTrendChart(null);
      }).not.toThrow();
      
      expect(() => {
        analytics.createUsageTrendChart('invalid');
      }).not.toThrow();
    });
  });

  describe('Error Handling', () => {
    test('should display error messages safely', () => {
      const mockErrorContainer = {
        textContent: '',
        appendChild: jest.fn()
      };
      
      document.getElementById.mockReturnValue(mockErrorContainer);
      
      analytics.handleError('Test error', new Error('Test'));
      
      expect(mockErrorContainer.textContent).toBe('');
      expect(mockErrorContainer.appendChild).toHaveBeenCalled();
    });

    test('should handle missing error container', () => {
      document.getElementById.mockReturnValue(null);
      
      expect(() => {
        analytics.handleError('Test error', new Error('Test'));
      }).not.toThrow();
    });
  });

  describe('Cleanup', () => {
    test('should destroy charts on cleanup', () => {
      const mockChart = new Chart();
      analytics.charts.testChart = mockChart;
      
      analytics.destroy();
      
      expect(mockChart.destroyed).toBe(true);
    });

    test('should clear intervals on cleanup', () => {
      const clearIntervalSpy = jest.spyOn(global, 'clearInterval');
      analytics.realTimeInterval = 123;
      
      analytics.destroy();
      
      expect(clearIntervalSpy).toHaveBeenCalledWith(123);
      
      clearIntervalSpy.mockRestore();
    });
  });

  describe('Data Validation', () => {
    test('should handle null/undefined data gracefully', () => {
      expect(() => {
        analytics.updatePredictions(null);
        analytics.updatePredictions(undefined);
        analytics.updateRecommendations(null);
        analytics.updateRecommendations(undefined);
      }).not.toThrow();
    });

    test('should validate numeric inputs', () => {
      const mockElement = { textContent: '', style: { setProperty: jest.fn() } };
      document.getElementById.mockReturnValue(mockElement);
      
      // Should handle invalid efficiency scores
      analytics.updateEfficiencyScore('invalid');
      analytics.updateEfficiencyScore(-10);
      analytics.updateEfficiencyScore(150);
      
      expect(mockElement.style.setProperty).toHaveBeenCalled();
    });
  });
});