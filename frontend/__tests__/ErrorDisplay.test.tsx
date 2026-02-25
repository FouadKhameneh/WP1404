import { render, screen, fireEvent } from "@testing-library/react";
import { ErrorDisplay } from "@/features/error/ErrorDisplay";

describe("ErrorDisplay", () => {
  it("renders message and optional retry button", () => {
    render(<ErrorDisplay message="Something failed" onRetry={() => {}} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Something failed");
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });

  it("calls onRetry when retry is clicked", () => {
    const onRetry = jest.fn();
    render(<ErrorDisplay message="Error" onRetry={onRetry} />);
    fireEvent.click(screen.getByRole("button", { name: /retry/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
