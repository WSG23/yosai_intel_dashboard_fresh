// Add custom Cypress commands
import { Config } from 'axe-core'

declare global {
  namespace Cypress {
    interface Chainable {
      injectAxeAndCheck(options?: Partial<Config>): Chainable<void>
    }
  }
}

// Inject axe-core and run accessibility checks
Cypress.Commands.add('injectAxeAndCheck', (options = {}) => {
  cy.injectAxe()
  cy.checkA11y(null, {
    runOnly: ['wcag2a', 'wcag2aa'],
    ...options
  })
})
