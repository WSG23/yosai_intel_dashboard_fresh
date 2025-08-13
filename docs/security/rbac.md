# RBAC Policy

This document outlines the role-based access control (RBAC) model used by the gateway.

## Role Matrix

| Role   | Permissions                       | Description |
|--------|-----------------------------------|-------------|
| admin  | doors.control, analytics.read, events.write | Full administrative access to all gateway functions. |
| analyst| analytics.read                    | View analytics data. |
| operator| doors.control                   | Manage door access and control systems. |
| auditor| events.write                     | Publish and audit event streams. |

## Rationale

Roles are designed to follow the principle of least privilege. Each role is granted only the permissions necessary to perform its duties, limiting potential impact from compromised credentials. Administrative endpoints such as breaker metrics and the `/admin` routes require the `admin` role to prevent unauthorized operational changes.

