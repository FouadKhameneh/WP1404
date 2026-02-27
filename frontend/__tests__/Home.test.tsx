import { render, screen, waitFor } from "@testing-library/react";
import Home from "@/app/page";

describe("Home page", () => {
  it("renders welcome and navigation links", async () => {
    render(<Home />);
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /Police Digital Operations/i })).toBeInTheDocument();
    });
    expect(screen.getByRole("link", { name: /ورود/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /ثبت‌نام/i })).toBeInTheDocument();
  });
});
