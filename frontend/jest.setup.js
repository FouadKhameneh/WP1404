import "@testing-library/jest-dom";

// Mock fetch so API calls in components don't hit the network or crash.
// Tests needing specific behavior (e.g. api.test) override in beforeAll.
const defaultFetchMock = () =>
  Promise.resolve({
    ok: true,
    status: 200,
    headers: new Headers({ "content-type": "application/json" }),
    json: async () => ({}),
  });
globalThis.fetch = jest.fn(defaultFetchMock);
