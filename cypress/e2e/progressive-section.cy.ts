/// <reference types="cypress" />

describe('ProgressiveSection accessibility', () => {
  it('hides content from screen readers until expanded', () => {
    cy.visit('/analytics');
    cy.get('#drilldown-metrics')
      .should('have.attr', 'aria-hidden', 'true')
      .and('not.be.visible');
    cy.contains('button', 'Drill-down Metrics').click();
    cy.get('#drilldown-metrics')
      .should('have.attr', 'aria-hidden', 'false')
      .and('be.visible');
  });
});
