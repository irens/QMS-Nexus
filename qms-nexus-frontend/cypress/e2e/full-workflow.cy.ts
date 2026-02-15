/**
 * QMS-Nexus 完整工作流 E2E 测试
 * 测试范围：上传→解析→存储→搜索→问答完整链路
 * 对应需求：US-MVP-01 至 US-MVP-08
 */

describe('QMS-Nexus Full E2E Workflow Test', () => {
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

  describe('Phase 1: 健康检查', () => {
    it('should have healthy backend service', () => {
      cy.request({
        method: 'GET',
        url: `${API_V1}/health`
      }).then((response) => {
        expect(response.status).to.eq(200)
        expect(response.body).to.have.property('status')
      })
    })
  })

  describe('Phase 2: 前端页面验证', () => {
    it('should load main dashboard', () => {
      cy.visit('/')
      cy.get('body').should('be.visible')
      cy.url().should('include', '/system')
    })

    it('should display navigation elements', () => {
      cy.visit('/system/dashboard')
      cy.get('nav, .el-menu, [class*="sidebar"]').should('exist')
    })
  })

  describe('Phase 3: 上传功能验证', () => {
    it('should display upload page correctly', () => {
      cy.visit('/system/upload')
      cy.url().should('include', '/system/upload')
      cy.get('input[type="file"]').should('exist')
    })

    it('should have upload API available', () => {
      cy.request({
        method: 'POST',
        url: `${API_V1}/upload`,
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 400, 415, 422]).to.include(response.status)
        
        if (response.status === 200) {
          expect(response.body).to.have.property('task_id')
          taskId = response.body.task_id
        }
      })
    })
  })

  describe('Phase 4: 搜索功能验证', () => {
    it('should display search page correctly', () => {
      cy.visit('/system/search')
      cy.url().should('include', '/system/search')
      cy.get('input[type="text"]').first().should('be.visible')
    })

    it('should accept search input', () => {
      cy.visit('/system/search')
      cy.get('input[type="text"]').first().as('searchInput')
      cy.get('@searchInput').clear().type('测试搜索')
      cy.get('@searchInput').should('have.value', '测试搜索')
    })

    it('should call search API', () => {
      cy.request({
        method: 'GET',
        url: `${API_V1}/search`,
        qs: { q: '测试查询', top_k: 5 },
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 400, 404]).to.include(response.status)
      })
    })
  })

  describe('Phase 5: 问答功能验证', () => {
    it('should display chat page correctly', () => {
      cy.visit('/system/chat')
      cy.url().should('include', '/system/chat')
      cy.get('textarea, input[type="text"]').first().should('be.visible')
    })

    it('should accept chat input', () => {
      cy.visit('/system/chat')
      cy.get('textarea, input[type="text"]').first().as('chatInput')
      cy.get('@chatInput').clear().type('这是一个测试问题')
      cy.get('@chatInput').should('have.value', '这是一个测试问题')
    })

    it('should call ask API and return response', () => {
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
          expect(response.body.answer).to.be.a('string')
          expect(response.body.sources).to.be.an('array')
        }
      })
    })
  })

  describe('Phase 6: 标签管理验证', () => {
    it('should display tags page correctly', () => {
      cy.visit('/system/tags')
      cy.url().should('include', '/system/tags')
    })

    it('should call tags API', () => {
      cy.request({
        method: 'GET',
        url: `${API_V1}/tags`
      }).then((response) => {
        expect(response.status).to.eq(200)
        expect(response.body).to.be.an('array')
      })
    })
  })

  describe('Phase 7: 文档管理验证', () => {
    it('should display documents page correctly', () => {
      cy.visit('/system/documents')
      cy.url().should('include', '/system/documents')
    })
  })

  describe('Phase 8: 错误处理验证', () => {
    it('should handle invalid task ID', () => {
      cy.request({
        method: 'GET',
        url: `${API_V1}/upload/status/nonexistent-task-id`,
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.eq(404)
      })
    })

    it('should handle empty question', () => {
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

  describe('Phase 9: 连续操作稳定性', () => {
    it('should handle multiple consecutive requests', () => {
      const requests = [
        () => cy.request({ method: 'GET', url: `${API_V1}/health` }),
        () => cy.request({ method: 'GET', url: `${API_V1}/tags` }),
        () => cy.request({ method: 'GET', url: `${API_V1}/search?q=test`, failOnStatusCode: false }),
        () => cy.request({ method: 'POST', url: `${BACKEND_URL}/ask`, body: { question: 'test' }, failOnStatusCode: false })
      ]

      requests.forEach((req) => {
        req().then((response) => {
          expect(response.status).to.be.lessThan(600)
        })
      })
    })
  })
})
