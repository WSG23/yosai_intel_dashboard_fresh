/// <reference types="cypress" />

describe('Static page accessibility', () => {
  it('has no detectable accessibility violations', () => {
    cy.visit('cypress/fixtures/a11y.html')
    cy.injectAxeAndCheck()
  })
})
