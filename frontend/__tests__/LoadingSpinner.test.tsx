import { render, screen } from "@testing-library/react";
import { LoadingSpinner, PageLoading } from "@/features/loading/LoadingSpinner";

describe("LoadingSpinner", () => {
  it("renders with aria label", () => {
    render(<LoadingSpinner />);
    expect(screen.getByRole("status", { name: /loading/i })).toBeInTheDocument();
  });
});

describe("PageLoading", () => {
  it("renders loading text", () => {
    render(<PageLoading />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
});
