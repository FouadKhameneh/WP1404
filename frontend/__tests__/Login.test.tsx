import { render, screen } from "@testing-library/react";
import { AuthProvider } from "@/context/AuthContext";
import LoginPage from "@/app/(auth)/login/page";

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn(), prefetch: jest.fn() }),
}));

describe("Login page", () => {
  it("renders login form with identifier and password", () => {
    render(
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    );
    expect(screen.getByRole("heading", { name: /ورود/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/رمز عبور/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /ورود/i })).toBeInTheDocument();
  });
});
