module.exports = {
    testEnvironment: 'jsdom',
    testMatch: ['**/tests/frontend/unit/**/*.test.js'],
    setupFilesAfterEnv: ['<rootDir>/tests/frontend/setup.js'],
    moduleNameMapper: {
        '\\.(css|less|scss|sass)$': '<rootDir>/tests/frontend/mocks/styleMock.js',
        '\\.(gif|ttf|eot|svg|png)$': '<rootDir>/tests/frontend/mocks/fileMock.js'
    }
};
