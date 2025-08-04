# Mobile Device Testing Matrix

To ensure consistent behavior across a range of devices, our BrowserStack
device lab covers the following targets:

| Device             | Resolution (px) | OS        | Notes                     |
|--------------------|----------------|-----------|---------------------------|
| iPhone SE (2nd Gen)| 750 x 1334     | iOS 14    | Small phone baseline      |
| iPhone 12          | 1170 x 2532    | iOS 15    | Modern high‑dpi handset  |
| Google Pixel 5     | 1080 x 2340    | Android 12| Representative Android     |
| iPad Mini          | 768 x 1024     | iPadOS 14 | Tablet breakpoint         |
| iPad Pro 12.9      | 2048 x 2732    | iPadOS 15 | Large tablet/desktop-ish  |

Accessibility checks with `cypress-axe` run across these breakpoints via
`cy.viewport` settings defined in the mobile accessibility test suite.

