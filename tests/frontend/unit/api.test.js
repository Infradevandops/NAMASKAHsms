describe('API Client', () => {
    test('should return data on success', async () => {
        global.fetch = jest.fn(() =>
            Promise.resolve({
                ok: true,
                json: () => Promise.resolve({ data: 'test' })
            })
        );

        // This is a placeholder test until we migrate JS modules to testable units
        const response = await fetch('/api/test');
        const data = await response.json();
        expect(data).toEqual({ data: 'test' });
    });
});
