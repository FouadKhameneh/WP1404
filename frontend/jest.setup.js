import "@testing-library/jest-dom";

if (typeof globalThis.fetch === "undefined") {
  globalThis.fetch = jest.fn();
}
