export type Session = { username: string; demo: boolean };
export type Order = {
  name: string;
  price: number;
  purchase_date: string;
  reason: "eligible" | "future purchase" | "outside 30-day window";
  refundable: boolean;
};
export type RefundLine = {
  name: string;
  amount: number;
  reason: "eligible" | "not purchased" | "future purchase" | "outside 30-day window";
};
export type Quote = { status: string; amount: number; items: RefundLine[]; as_of: string };
export type Ticket = {
  status: "success";
  ticket_id: string;
  amount: number;
  simulated: true;
  created_at: string;
  quote: Quote;
};
export type ChatResult = {
  answer: string;
  conversation: boolean;
  tools: { name: string; arguments: Record<string, unknown> }[];
};

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail;
    const message =
      typeof detail === "string"
        ? detail
        : detail?.message || "The request could not be completed";
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  session: () => request<Session>("/api/auth/session"),
  login: (username: string, password: string) =>
    request<Session>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  logout: () => request<void>("/api/auth/logout", { method: "DELETE" }),
  orders: () => request<Order[]>("/api/orders"),
  quote: (items: string[]) =>
    request<Quote>("/api/refunds/quote", {
      method: "POST",
      body: JSON.stringify({ items }),
    }),
  ticket: (items: string[], refundAmount: number) =>
    request<Ticket>("/api/refunds/tickets", {
      method: "POST",
      body: JSON.stringify({ items, refund_amount: refundAmount }),
    }),
  chat: (message: string, conversationId: string) =>
    request<ChatResult>("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message, conversation_id: conversationId }),
    }),
};
