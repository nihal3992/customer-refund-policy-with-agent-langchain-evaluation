import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";

describe("portfolio experience", () => {
  afterEach(() => vi.restoreAllMocks());

  it("introduces the product and links to the interactive demo", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Sign in required" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      }),
    );
    render(<MemoryRouter><App /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText(/Refund decisions you can inspect/i)).toBeInTheDocument());
    expect(screen.getAllByRole("link", { name: /demo|refund flow/i }).length).toBeGreaterThan(0);
    expect(screen.getByText(/The model proposes. The policy decides./i)).toBeInTheDocument();
  });
});
