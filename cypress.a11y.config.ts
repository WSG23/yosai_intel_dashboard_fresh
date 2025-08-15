import { defineConfig } from 'cypress'

export default defineConfig({
  e2e: {
    // The accessibility suite runs entirely against static fixtures,
    // so no baseUrl is required. Removing it prevents Cypress from
    // trying to verify a running server before tests execute.
    supportFile: 'cypress/support/e2e.ts',
    specPattern: 'cypress/e2e/**/*.cy.{js,ts}',
    setupNodeEvents() {
      // A placeholder is kept for future node event listeners such as
      // accessibility logging. The actual axe checks are configured in
      // the support file via `cypress-axe` commands.
    }
  }
})
