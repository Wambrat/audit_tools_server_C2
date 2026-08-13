/**
 * Configuration Jest setup pour les tests frontend
 * Initialise l'environnement de test
 */

// Mock de window.fetch
global.fetch = jest.fn();

// Mock de console
global.console = {
  ...console,
  error: jest.fn(),
  warn: jest.fn(),
  log: jest.fn()
};

// Mock de localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};
global.localStorage = localStorageMock;

// Mock de sessionStorage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};
global.sessionStorage = sessionStorageMock;

// Mock de window.location
delete window.location;
window.location = {
  href: '',
  pathname: '/',
  search: '',
  hash: '',
  reload: jest.fn()
};

// Augmenter les timeouts pour les tests asynchrones
jest.setTimeout(10000);
