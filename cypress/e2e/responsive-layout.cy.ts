/// <reference types="cypress" />

describe('Responsive layout screenshots', () => {
  const devices: Cypress.ViewportPreset[] = ['iphone-5', 'iphone-xr'];
  const pages = ['/', '/upload'];

  devices.forEach((device) => {
    pages.forEach((page) => {
      it(`captures ${page} on ${device}`, () => {
        const screenshotName = `${page.replace(/\//g, '')}-${device}`;
        cy.viewport(device);
        cy.visit(page);
        cy.get('body').should('be.visible');
        cy.screenshot(screenshotName);
        cy.readFile(
          `cypress/screenshots/responsive-layout.cy.ts/${screenshotName}.png`,
          'binary'
        ).should('exist');
      });
    });
  });
});
