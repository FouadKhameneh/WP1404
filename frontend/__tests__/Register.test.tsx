import { render, screen } from "@testing-library/react";
import { AuthProvider } from "@/context/AuthContext";
import RegisterPage from "@/app/(auth)/register/page";

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn(), prefetch: jest.fn() }),
}));

describe("Register page", () => {
  it("renders register form with required fields", () => {
    render(
      <AuthProvider>
        <RegisterPage />
      </AuthProvider>
    );
    expect(screen.getByRole("heading", { name: /ثبت‌نام/i })).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/یکتا، بدون فاصله/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/example@domain.com/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /ثبت‌نام/i })).toBeInTheDocument();
    expect(screen.getAllByText(/رمز عبور/i).length).toBeGreaterThanOrEqual(1);
  });
});
