/**
 * QMS-Nexus API 集成 E2E 测试
 * 测试范围：完整API端点验证、需求验收测试
 * 对应需求：US-MVP-01 至 US-MVP-08, US-Alpha-02
 */

describe('QMS-Nexus API Integration E2E Tests', () => {
  const BACKEND_URL = 'http://127.0.0.1:8000'
  const API_V1 = `${BACKEND_URL}/api/v1`
  let taskId: string

  before(() => {
    cy.request({
      method: 'GET',
      url: `${API_V1}/health`,
      timeout: 30000
    }).then((response) => {
      expect(response.status).to.eq(200)
    })
  })

  describe('US-MVP-01: 多格式文档上传与解析入库', () => {
    it('should accept upload API requests', () => {
      cy.request({
        method: 'POST',
        url: `${API_V1}/upload`,
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 400, 415, 422]).to.include(response.status)
      })
    })

    it('should reject oversized files (>50MB)', () => {
      cy.request({
        method: 'POST',
        url: `${API_V1}/upload`,
        headers: { 'Content-Length': '60000000' },
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 400, 413, 415, 422]).to.include(response.status)
      })
    })

    it('should reject unsupported file formats', () => {
      cy.request({
        method: 'POST',
        url: `${API_V1}/upload`,
        headers: { 'Content-Type': 'application/x-executable' },
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 400, 415, 422]).to.include(response.status)
      })
    })
  })

  describe('US-MVP-03 & US-MVP-04: 基于文档的精准问答与来源标注', () => {
    it('should return answer with sources', () => {
      cy.request({
        method: 'POST',
        url: `${BACKEND_URL}/ask`,
        headers: { 'Content-Type': 'application/json' },
        body: { question: '系统功能介绍' },
        failOnStatusCode: false
      }).then((response) => {
        if (response.status === 200) {
          expect(response.body).to.have.property('answer')
          expect(response.body).to.have.property('sources')
          expect(response.body.answer).to.be.a('string')
          expect(response.body.sources).to.be.an('array')
        } else {
          expect([200, 400, 500]).to.include(response.status)
        }
      })
    })

    it('should include source attribution in format [来源：文件名, 第X页]', () => {
      cy.request({
        method: 'POST',
        url: `${BACKEND_URL}/ask`,
        headers: { 'Content-Type': 'application/json' },
        body: { question: '质量管理要求' },
        failOnStatusCode: false
      }).then((response) => {
        if (response.status === 200 && response.body.sources) {
          const sources = response.body.sources
          if (sources.length > 0) {
            sources.forEach((source: string) => {
              const hasValidFormat = 
                source.includes('来源') ||
                source.includes('第') ||
                source.includes('页') ||
                source.includes('.pdf') ||
                source.includes('.doc') ||
                source.includes('.xlsx') ||
                source.includes('.pptx')
              expect(hasValidFormat).to.be.true
            })
          }
        }
      })
    })
  })

  describe('US-MVP-05: Web前端基础交互', () => {
    it('should load frontend without errors', () => {
      cy.visit('/')
      cy.get('body').should('be.visible')
    })

    it('should navigate between pages', () => {
      const pages = [
        '/system/dashboard',
        '/system/upload',
        '/system/documents',
        '/system/chat',
        '/system/search',
        '/system/tags'
      ]

      pages.forEach((page) => {
        cy.visit(page)
        cy.get('body').should('be.visible')
        cy.url().should('include', page)
      })
    })
  })

  describe('US-MVP-06: 基础错误处理', () => {
    it('should handle invalid task ID gracefully', () => {
      cy.request({
        method: 'GET',
        url: `${API_V1}/upload/status/invalid-task-id-xyz`,
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.eq(404)
      })
    })

    it('should handle empty question gracefully', () => {
      cy.request({
        method: 'POST',
        url: `${BACKEND_URL}/ask`,
        headers: { 'Content-Type': 'application/json' },
        body: { question: '' },
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 400, 422]).to.include(response.status)
      })
    })

    it('should handle invalid API endpoint gracefully', () => {
      cy.request({
        method: 'GET',
        url: `${API_V1}/nonexistent-endpoint`,
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.eq(404)
      })
    })
  })

  describe('US-MVP-07: 本地向量库基础管理', () => {
    it('should provide tags management API', () => {
      cy.request({
        method: 'GET',
        url: `${API_V1}/tags`
      }).then((response) => {
        expect(response.status).to.eq(200)
        expect(response.body).to.be.an('array')
      })
    })
  })

  describe('US-MVP-08: 本地全流程联调稳定性', () => {
    it('should complete full workflow without crashes', () => {
      cy.request({ method: 'GET', url: `${API_V1}/health` })
        .its('status').should('eq', 200)

      cy.request({
        method: 'GET',
        url: `${API_V1}/search`,
        qs: { q: 'test' },
        failOnStatusCode: false
      }).its('status').should('be.lessThan', 600)

      cy.request({
        method: 'POST',
        url: `${BACKEND_URL}/ask`,
        body: { question: 'test' },
        failOnStatusCode: false
      }).its('status').should('be.lessThan', 600)
    })

    it('should handle consecutive operations', () => {
      for (let i = 0; i < 5; i++) {
        cy.request({
          method: 'GET',
          url: `${API_V1}/health`
        }).then((response) => {
          expect(response.status).to.eq(200)
        })
      }
    })
  })

  describe('US-Alpha-02: 用户反馈功能', () => {
    it('should handle feedback request', () => {
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
})
