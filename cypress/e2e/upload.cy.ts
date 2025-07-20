/// <reference types="cypress" />

describe('File Upload Flow', () => {
  beforeEach(() => {
    cy.intercept('POST', '/api/v1/upload', {
      statusCode: 200,
      body: {
        requiresColumnMapping: true,
        fileData: {
          filename: 'sample.csv',
          columns: ['person_id', 'door_id', 'timestamp', 'access_result'],
          ai_suggestions: {
            person_id: { field: 'person_id', confidence: 0.95 },
            door_id: { field: 'door_id', confidence: 0.9 },
            timestamp: { field: 'timestamp', confidence: 0.9 },
            access_result: { field: 'access_result', confidence: 0.9 }
          }
        }
      }
    }).as('upload')
    cy.visit('/')
  })

  it('uploads a file and shows mapping modal', () => {
    cy.get('input[type="file"]').selectFile({
      contents: 'person_id,door_id,timestamp,access_result\n1,101,2024-01-01T00:00:00Z,granted\n',
      fileName: 'sample.csv',
      mimeType: 'text/csv'
    }, { force: true })
    cy.contains('Upload All').click()
    cy.wait('@upload')
    cy.contains('AI Column Mapping').should('be.visible')
  })

  it('maps columns and completes upload', () => {
    cy.get('input[type="file"]').selectFile({
      contents: 'person_id,door_id,timestamp,access_result\n1,101,2024-01-01T00:00:00Z,granted\n',
      fileName: 'sample.csv',
      mimeType: 'text/csv'
    }, { force: true })
    cy.contains('Upload All').click()
    cy.wait('@upload')
    cy.contains('AI Column Mapping').should('be.visible')
    cy.contains('Confirm & Continue').click()
    cy.contains('AI Column Mapping').should('not.exist')
    cy.get('.progress-bar-large .progress-fill-large').should('have.attr', 'style', 'width: 100%')
  })
})
