import React from 'react';

export const MockLink: React.FC<
  React.AnchorHTMLAttributes<HTMLAnchorElement>
> = ({ children, ...props }) => <a {...props}>{children}</a>;

export const MockMemoryRouter: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => <div>{children}</div>;
