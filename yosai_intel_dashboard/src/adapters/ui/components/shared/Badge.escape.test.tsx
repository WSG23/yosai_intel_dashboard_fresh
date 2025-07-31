import { render, screen } from "@testing-library/react";
import { Badge } from "./Badge";

test("escapes HTML content", () => {
  const malicious = "<img src=x onerror=alert(1) />";
  render(<Badge>{malicious}</Badge>);
  // the text should render literally and no img element should exist
  expect(screen.getByText(malicious)).toBeInTheDocument();
  expect(screen.queryByRole("img")).not.toBeInTheDocument();
});
