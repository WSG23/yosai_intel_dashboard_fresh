import { defineConfig } from 'cypress'

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    supportFile: 'cypress/support/e2e.ts',
    specPattern: 'cypress/e2e/**/*.cy.{js,ts}',
    // Enable BrowserStack plugin when credentials are provided
    setupNodeEvents(on, config) {
      if (
        process.env.BROWSERSTACK_USERNAME &&
        process.env.BROWSERSTACK_ACCESS_KEY
      ) {
        // eslint-disable-next-line @typescript-eslint/no-var-requires
        require('@browserstack/cypress-cli/lib/plugin')(on, config)
      }
      return config
    }
  }
})
