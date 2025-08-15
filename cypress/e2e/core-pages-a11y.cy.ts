/// <reference types="cypress" />

describe('Core page accessibility', () => {
  const pages = ['/', '/upload', '/progressive-section'];

  pages.forEach((page) => {
    it(`has no detectable accessibility violations on ${page}`, () => {
      cy.visit(page);
      cy.injectAxeAndCheck();
    });
  });
});
