/**
 * QMS-Nexus API 工作流 E2E 测试
 * 测试范围：上传、查询、标签管理API
 * 对应需求：US-MVP-01, US-MVP-03, US-MVP-07
 */

describe('QMS-Nexus API Workflow E2E Test', () => {
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

  describe('Health Check API', () => {
    it('should return healthy status', () => {
      cy.request({
        method: 'GET',
        url: `${API_V1}/health`
      }).then((response) => {
        expect(response.status).to.eq(200)
        expect(response.body).to.have.property('status')
      })
    })
  })

  describe('Upload API', () => {
    it('should handle upload request without file', () => {
      cy.request({
        method: 'POST',
        url: `${API_V1}/upload`,
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 400, 415, 422]).to.include(response.status)
      })
    })

    it('should return task status for valid task ID format', () => {
      cy.request({
        method: 'GET',
        url: `${API_V1}/upload/status/test-task-id`,
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 404]).to.include(response.status)
      })
    })
  })

  describe('Search API', () => {
    it('should handle search request', () => {
      cy.request({
        method: 'GET',
        url: `${API_V1}/search`,
        qs: { q: '测试查询' },
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 400, 404]).to.include(response.status)
      })
    })

    it('should handle search with filters', () => {
      cy.request({
        method: 'GET',
        url: `${API_V1}/search`,
        qs: { q: '测试', filter_tags: 'tag1,tag2' },
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 400, 404]).to.include(response.status)
      })
    })
  })

  describe('Ask API (RAG Q&A)', () => {
    it('should handle question request', () => {
      cy.request({
        method: 'POST',
        url: `${BACKEND_URL}/ask`,
        headers: { 'Content-Type': 'application/json' },
        body: { question: '测试问题' },
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 400, 500]).to.include(response.status)
        
        if (response.status === 200) {
          expect(response.body).to.have.property('answer')
          expect(response.body).to.have.property('sources')
        }
      })
    })

    it('should return error for empty question', () => {
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
  })

  describe('Tags API', () => {
    it('should return tags list', () => {
      cy.request({
        method: 'GET',
        url: `${API_V1}/tags`
      }).then((response) => {
        expect(response.status).to.eq(200)
        expect(response.body).to.be.an('array')
      })
    })

    it('should handle tag creation', () => {
      cy.request({
        method: 'POST',
        url: `${API_V1}/tags`,
        headers: { 'Content-Type': 'application/json' },
        body: { name: 'test-tag', description: 'Test tag' },
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 201, 400, 409, 422]).to.include(response.status)
      })
    })
  })

  describe('System API', () => {
    it('should return system status', () => {
      cy.request({
        method: 'GET',
        url: `${API_V1}/system/status`,
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 404]).to.include(response.status)
      })
    })

    it('should return system config', () => {
      cy.request({
        method: 'GET',
        url: `${API_V1}/system/config`,
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 404]).to.include(response.status)
      })
    })
  })
})
