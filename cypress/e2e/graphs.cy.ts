/// <reference types="cypress" />

describe('Graph visualizations', () => {
  beforeEach(() => {
    cy.visit('/graphs');
  });

  it('renders and interacts with network graph', () => {
    cy.get('select').select('Network Graph');
    cy.get('div[aria-label="Network Relationships visualization"]').within(() => {
      cy.get('svg').should('have.attr', 'aria-hidden', 'true');
      cy.get('svg circle').first().click().should('have.attr', 'fill', 'red');
    });
    cy.contains('Show Table').click();
    cy.get('table').should('exist');
    cy.contains('Show Chart').click();
    cy.get('div[aria-label="Network Relationships visualization"]').should('exist');
  });

  it('renders 3D facility layout', () => {
    cy.get('select').select('Facility Layout');
    cy.get('div[aria-label="3D Facility Layout visualization"]').within(() => {
      cy.get('canvas').should('have.attr', 'aria-hidden', 'true');
    });
    cy.contains('Show Table').click();
    cy.get('table').should('exist');
  });
});
