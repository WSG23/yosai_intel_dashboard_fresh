/// <reference types="cypress" />

describe('Mobile accessibility checks', () => {
  const devices: Cypress.ViewportPreset[] = [
    'iphone-5',
    'iphone-8',
    'iphone-xr',
    'ipad-2',
    'ipad-mini'
  ]

  devices.forEach(device => {
    it(`has no detectable accessibility violations on ${device}`, () => {
      cy.viewport(device)
      cy.visit('/')
      cy.injectAxeAndCheck()
    })
  })
})

