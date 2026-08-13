/**
 * Configuration Jest pour les tests du frontend
 */

module.exports = {
  testEnvironment: 'jsdom',
  testMatch: ['**/test/frontend/test_*.js'],
  collectCoverageFrom: [
    'web/js/**/*.js',
    '!web/js/**/*.min.js'
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70
    }
  },
  setupFilesAfterEnv: ['<rootDir>/test/frontend/setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/web/$1'
  },
  transform: {
    '^.+\\.js$': 'babel-jest'
  },
  testTimeout: 10000
};
