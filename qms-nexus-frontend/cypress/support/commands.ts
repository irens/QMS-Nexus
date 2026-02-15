/// <reference types="cypress" />

declare global {
  namespace Cypress {
    interface Chainable {
      /**
       * 等待后端服务就绪
       */
      waitForBackend(timeout?: number): Chainable<void>
      /**
       * 上传测试文件
       */
      uploadTestFile(filePath: string): Chainable<void>
      /**
       * 执行搜索操作
       */
      performSearch(query: string): Chainable<void>
      /**
       * 发送聊天消息
       */
      sendChatMessage(message: string): Chainable<void>
    }
  }
}

Cypress.Commands.add('waitForBackend', (timeout = 30000) => {
  const startTime = Date.now()
  
  function checkHealth(): Cypress.Chainable<void> {
    return cy.request({
      method: 'GET',
      url: 'http://127.0.0.1:8000/api/v1/health',
      failOnStatusCode: false,
      timeout: 5000
    }).then((response) => {
      if (response.status === 200) {
        return
      }
      
      const elapsed = Date.now() - startTime
      if (elapsed > timeout) {
        throw new Error(`Backend service not available after ${timeout}ms`)
      }
      
      cy.wait(1000)
      return checkHealth()
    })
  }
  
  return checkHealth()
})

Cypress.Commands.add('uploadTestFile', (filePath: string) => {
  cy.get('input[type="file"]').selectFile(filePath, { force: true })
})

Cypress.Commands.add('performSearch', (query: string) => {
  cy.get('[data-testid="search-input"]')
    .clear()
    .type(query)
  cy.get('[data-testid="search-button"]').click()
})

Cypress.Commands.add('sendChatMessage', (message: string) => {
  cy.get('[data-testid="chat-input"]')
    .clear()
    .type(message)
  cy.get('[data-testid="send-button"]').click()
})

export {}
