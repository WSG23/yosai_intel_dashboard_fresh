# Component Styling Guidelines

This project follows the [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/) for consistent look and feel across the dashboard. Below are key points to keep in mind when creating UI components.

- **Clarity** – Each component should clearly communicate its purpose. Use straightforward labels and standard controls.
- **Deference** – UI chrome stays light and unobtrusive, letting user data take center stage. Avoid heavy borders or shadows.
- **Depth** – Use layering and subtle animation to convey hierarchy and transitions.
- **Consistency** – Layouts, fonts, and colors should remain consistent across pages. Reuse existing styles when possible.
- **Feedback** – Provide immediate feedback for user actions, such as highlighting selected items or showing progress indicators.

## Component Usage Examples
- **Button** – Apply the primary style for main actions and a secondary style for alternatives. Example: `<Button variant="primary">Save</Button>`.
- **Input Field** – Pair labels with inputs and provide helper text for format hints. Example: `<TextField label="Email" type="email" />`.
- **Modal** – Use modals for short, focused tasks that require user confirmation without leaving the current screen.

## Accessibility Notes
- Use semantic elements and provide `aria-label` or `aria-describedby` attributes where appropriate.
- Ensure all interactive components are reachable via keyboard and include visible focus states.
- Maintain color contrast ratios that meet WCAG AA guidelines.

Refer to Apple's documentation for more details on color usage, typography, and controls.
