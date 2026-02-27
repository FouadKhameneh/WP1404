import { render, screen } from "@testing-library/react";
import { Skeleton, SkeletonCard, SkeletonList } from "@/features/loading/Skeleton";

describe("Skeleton", () => {
  it("renders Skeleton with default props", () => {
    const { container } = render(<Skeleton />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it("renders SkeletonCard", () => {
    const { container } = render(<SkeletonCard />);
    expect(container.querySelector(".card")).toBeInTheDocument();
  });

  it("renders SkeletonList with default count", () => {
    const { container } = render(<SkeletonList />);
    const items = container.querySelectorAll("[style*='border-radius: 50%']");
    expect(items.length).toBe(5);
  });

  it("renders SkeletonList with custom count", () => {
    const { container } = render(<SkeletonList count={3} />);
    const items = container.querySelectorAll("[style*='border-radius: 50%']");
    expect(items.length).toBe(3);
  });
});
