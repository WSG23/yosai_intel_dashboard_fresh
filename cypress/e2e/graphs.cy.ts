/// <reference types="cypress" />

describe('Graph visualizations', () => {
  beforeEach(() => {
    cy.visit('/graphs');
  });

  it('renders and interacts with network graph', () => {
    cy.get('select').select('Network Graph');
    cy.get('svg circle').first().click().should('have.attr', 'fill', 'red');
    cy.contains('Show Table').click();
    cy.get('table').should('exist');
    cy.contains('Show Chart').click();
    cy.get('svg').should('exist');
  });

  it('renders 3D facility layout', () => {
    cy.get('select').select('Facility Layout');
    cy.get('canvas').should('exist');
    cy.contains('Show Table').click();
    cy.get('table').should('exist');
  });
});
