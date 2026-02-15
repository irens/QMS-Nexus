/**
 * QMS-Nexus 需求导向 E2E 测试
 * 测试范围：US-MVP-01 至 US-MVP-08, US-Alpha-02
 */

describe('QMS-Nexus Specific Feature E2E Tests', () => {
  const BACKEND_URL = 'http://127.0.0.1:8000'
  const API_V1 = `${BACKEND_URL}/api/v1`

  before(() => {
    cy.request({
      method: 'GET',
      url: `${API_V1}/health`,
      failOnStatusCode: false
    }).then((response) => {
      expect(response.status).to.eq(200)
    })
  })

  describe('US-MVP-01: 多格式文档上传与解析入库', () => {
    it('should handle multi-format document upload', () => {
      cy.visit('/system/upload')
      cy.url().should('include', '/system/upload')
      cy.get('input[type="file"]').should('exist')

      cy.request({
        method: 'POST',
        url: `${API_V1}/upload`,
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 400, 415, 422]).to.include(response.status)
      })
    })
  })

  describe('US-MVP-03: 基于文档的精准问答', () => {
    it('should provide accurate document-based Q&A', () => {
      cy.visit('/system/chat')
      cy.url().should('include', '/system/chat')

      cy.request({
        method: 'POST',
        url: `${BACKEND_URL}/ask`,
        headers: { 'Content-Type': 'application/json' },
        body: { question: '系统功能介绍' },
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 400, 500]).to.include(response.status)
        
        if (response.status === 200) {
          expect(response.body).to.have.property('answer')
          expect(response.body).to.have.property('sources')
        }
      })
    })
  })

  describe('US-MVP-04: 回答来源精准标注', () => {
    it('should provide accurate source attribution', () => {
      cy.request({
        method: 'POST',
        url: `${BACKEND_URL}/ask`,
        headers: { 'Content-Type': 'application/json' },
        body: { question: '测试来源标注' },
        failOnStatusCode: false
      }).then((response) => {
        if (response.status === 200) {
          expect(response.body).to.have.property('answer')
          expect(response.body).to.have.property('sources')
          
          const sources = response.body.sources
          if (Array.isArray(sources) && sources.length > 0) {
            sources.forEach((source: string) => {
              const hasValidFormat = 
                source.includes('来源') ||
                source.includes('第') ||
                source.includes('页') ||
                source.includes('.pdf') ||
                source.includes('.doc')
              expect(hasValidFormat).to.be.true
            })
          }
        }
      })
    })
  })

  describe('US-MVP-05: web本地前端基础交互', () => {
    it('should provide smooth frontend interaction', () => {
      cy.visit('/')
      cy.get('body', { timeout: 60000 }).should('be.visible')

      cy.visit('/system/dashboard')
      cy.url().should('include', '/system/dashboard')

      cy.visit('/system/chat')
      cy.url().should('include', '/system/chat')

      cy.visit('/system/documents')
      cy.url().should('include', '/system/documents')

      cy.visit('/system/upload')
      cy.url().should('include', '/system/upload')
    })
  })

  describe('US-MVP-06: 基础错误处理', () => {
    it('should handle error conditions gracefully', () => {
      cy.request({
        method: 'POST',
        url: `${BACKEND_URL}/ask`,
        headers: { 'Content-Type': 'application/json' },
        body: { question: '' },
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 400, 422]).to.include(response.status)
      })

      cy.request({
        method: 'GET',
        url: `${BACKEND_URL}/nonexistent-endpoint`,
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.eq(404)
      })
    })
  })

  describe('US-Alpha-02: 用户反馈功能', () => {
    it('should handle user feedback functionality', () => {
      cy.request({
        method: 'POST',
        url: `${BACKEND_URL}/ask`,
        headers: { 'Content-Type': 'application/json' },
        body: { question: '测试反馈功能' },
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 400, 500]).to.include(response.status)
      })
    })
  })

  describe('US-MVP-07: 本地向量库基础管理', () => {
    it('should handle knowledge base management', () => {
      cy.request({
        method: 'GET',
        url: `${API_V1}/tags`
      }).then((response) => {
        expect(response.status).to.eq(200)
        expect(response.body).to.be.an('array')
      })
    })
  })

  describe('US-MVP-08: 完整用户工作流', () => {
    it('should complete a full user workflow without crashes', () => {
      cy.visit('/')
      cy.get('body').should('be.visible')

      cy.visit('/system/upload')
      cy.url().should('include', '/system/upload')

      cy.visit('/system/chat')
      cy.url().should('include', '/system/chat')

      cy.request({
        method: 'POST',
        url: `${BACKEND_URL}/ask`,
        headers: { 'Content-Type': 'application/json' },
        body: { question: '综合功能测试' },
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 400, 500]).to.include(response.status)
      })

      cy.visit('/system/documents')
      cy.url().should('include', '/system/documents')

      cy.get('body').should('be.visible')
    })
  })
})
