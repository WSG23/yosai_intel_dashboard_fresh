/// <reference types="cypress" />

describe('Accessibility checks', () => {
  beforeEach(() => {
    cy.visit('/')
  })

  it('has no detectable accessibility violations on load', () => {
    cy.injectAxeAndCheck()
  })
})
