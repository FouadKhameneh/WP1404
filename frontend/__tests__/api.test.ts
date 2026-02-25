import { api } from "@/lib/api";

const fetchMock = jest.fn();
beforeAll(() => {
  (globalThis as unknown as { fetch: jest.Mock }).fetch = fetchMock;
});
afterAll(() => {
  delete (globalThis as unknown as { fetch?: unknown }).fetch;
});

describe("API client", () => {
  it("builds request with token in Authorization header", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 200,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ data: { id: 1 } }),
    } as Response);
    await api.get("/test/", "fake-token");
    expect(fetchMock).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Token fake-token",
        }),
      })
    );
  });

  it("returns error when response is not ok", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 403,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ error: { message: "Forbidden" } }),
    } as Response);
    const res = await api.get("/forbidden/");
    expect(res.status).toBe(403);
    expect(res.error?.message).toBe("Forbidden");
  });
});
