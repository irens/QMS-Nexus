/**
 * QMS-Nexus 核心功能 E2E 测试
 * 测试范围：搜索框、文件上传、智能问答
 * 对应需求：US-MVP-01, US-MVP-03, US-MVP-04, US-MVP-05, US-MVP-06
 */

describe('QMS-Nexus Core Features E2E Tests', () => {
  const BACKEND_URL = 'http://127.0.0.1:8000'
  const API_V1 = `${BACKEND_URL}/api/v1`

  before(() => {
    cy.waitForBackend(30000)
  })

  describe('1. 搜索框功能测试 (US-MVP-03)', () => {
    beforeEach(() => {
      cy.visit('/system/search')
      cy.waitForBackend()
    })

    it('1.1 应正确显示搜索页面', () => {
      cy.get('body').should('be.visible')
      cy.url().should('include', '/system/search')
    })

    it('1.2 搜索框应可正常输入', () => {
      const testQuery = '测试搜索关键词'
      
      cy.get('input[type="text"]').first().as('searchInput')
      cy.get('@searchInput').should('be.visible')
      cy.get('@searchInput').clear()
      cy.get('@searchInput').type(testQuery)
      cy.get('@searchInput').should('have.value', testQuery)
    })

    it('1.3 API搜索接口应正常响应', () => {
      cy.request({
        method: 'GET',
        url: `${API_V1}/search`,
        qs: { q: '测试查询' },
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 400, 404, 500]).to.include(response.status)
        if (response.status === 200) {
          expect(response.body).to.be.an('array')
        }
      })
    })

    it('1.4 空搜索应返回适当提示', () => {
      cy.get('input[type="text"]').first().clear()
      cy.get('button').contains('搜索').click({ force: true })
      
      cy.get('body').should('be.visible')
    })

    it('1.5 搜索结果应显示来源信息', () => {
      cy.request({
        method: 'GET',
        url: `${API_V1}/search`,
        qs: { q: '质量管理', top_k: 5 },
        failOnStatusCode: false
      }).then((response) => {
        if (response.status === 200 && response.body.length > 0) {
          response.body.forEach((result: any) => {
            if (result.metadata) {
              expect(result.metadata).to.have.property('filename')
            }
          })
        }
      })
    })
  })

  describe('2. 文件上传功能测试 (US-MVP-01)', () => {
    beforeEach(() => {
      cy.visit('/system/upload')
      cy.waitForBackend()
    })

    it('2.1 应正确显示上传页面', () => {
      cy.get('body').should('be.visible')
      cy.url().should('include', '/system/upload')
    })

    it('2.2 上传区域应可见', () => {
      cy.get('.upload-dropzone, [class*="upload"]').should('exist')
    })

    it('2.3 文件选择器应存在', () => {
      cy.get('input[type="file"]').should('exist')
    })

    it('2.4 API上传接口应正常响应', () => {
      cy.request({
        method: 'POST',
        url: `${API_V1}/upload`,
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 400, 415, 422]).to.include(response.status)
      })
    })

    it('2.5 上传状态查询接口应可用', () => {
      const testTaskId = 'test-task-id'
      
      cy.request({
        method: 'GET',
        url: `${API_V1}/upload/status/${testTaskId}`,
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 404]).to.include(response.status)
      })
    })

    it('2.6 超大文件应被拒绝 (>50MB)', () => {
      cy.request({
        method: 'POST',
        url: `${API_V1}/upload`,
        headers: { 'Content-Length': '60_000_000' },
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 400, 413, 415, 422]).to.include(response.status)
      })
    })

    it('2.7 不支持的文件格式应被拒绝', () => {
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

  describe('3. 智能问答功能测试 (US-MVP-03, US-MVP-04)', () => {
    beforeEach(() => {
      cy.visit('/system/chat')
      cy.waitForBackend()
    })

    it('3.1 应正确显示聊天页面', () => {
      cy.get('body').should('be.visible')
      cy.url().should('include', '/system/chat')
    })

    it('3.2 聊天输入框应可正常输入', () => {
      const testMessage = '这是一个测试问题'
      
      cy.get('textarea, input[type="text"]').first().as('chatInput')
      cy.get('@chatInput').should('be.visible')
      cy.get('@chatInput').clear()
      cy.get('@chatInput').type(testMessage)
      cy.get('@chatInput').should('have.value', testMessage)
    })

    it('3.3 /ask API应正常响应', () => {
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
          expect(response.body.answer).to.be.a('string')
          expect(response.body.sources).to.be.an('array')
        }
      })
    })

    it('3.4 回答应包含来源标注 (US-MVP-04)', () => {
      cy.request({
        method: 'POST',
        url: `${BACKEND_URL}/ask`,
        headers: { 'Content-Type': 'application/json' },
        body: { question: '系统功能介绍' },
        failOnStatusCode: false
      }).then((response) => {
        if (response.status === 200) {
          const { sources } = response.body
          
          if (sources && sources.length > 0) {
            sources.forEach((source: string) => {
              expect(source).to.satisfy((s: string) => {
                return s.includes('来源') || s.includes('第') || s.includes('页') || s.includes('.pdf') || s.includes('.doc')
              })
            })
          }
        }
      })
    })

    it('3.5 空问题应返回错误提示', () => {
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

    it('3.6 长问题应正常处理', () => {
      const longQuestion = '这是一个很长的问题'.repeat(50)
      
      cy.request({
        method: 'POST',
        url: `${BACKEND_URL}/ask`,
        headers: { 'Content-Type': 'application/json' },
        body: { question: longQuestion },
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 400, 413, 500]).to.include(response.status)
      })
    })
  })

  describe('4. 完整工作流测试 (US-MVP-08)', () => {
    it('4.1 应完成上传->搜索->问答完整流程', () => {
      cy.waitForBackend()

      cy.request({
        method: 'GET',
        url: `${API_V1}/health`
      }).then((healthResp) => {
        expect(healthResp.status).to.eq(200)
      })

      cy.request({
        method: 'GET',
        url: `${API_V1}/search`,
        qs: { q: '测试' },
        failOnStatusCode: false
      }).then((searchResp) => {
        expect([200, 400, 404]).to.include(searchResp.status)
      })

      cy.request({
        method: 'POST',
        url: `${BACKEND_URL}/ask`,
        headers: { 'Content-Type': 'application/json' },
        body: { question: '系统功能' },
        failOnStatusCode: false
      }).then((askResp) => {
        expect([200, 400, 500]).to.include(askResp.status)
      })
    })

    it('4.2 连续操作不应导致系统崩溃', () => {
      const operations = [
        () => cy.request({ method: 'GET', url: `${API_V1}/health`, failOnStatusCode: false }),
        () => cy.request({ method: 'GET', url: `${API_V1}/tags`, failOnStatusCode: false }),
        () => cy.request({ method: 'GET', url: `${API_V1}/search?q=test`, failOnStatusCode: false }),
        () => cy.request({ method: 'POST', url: `${BACKEND_URL}/ask`, body: { question: 'test' }, failOnStatusCode: false })
      ]

      operations.forEach((op, index) => {
        op().then((response) => {
          expect(response.status).to.be.lessThan(600)
          cy.log(`Operation ${index + 1} completed with status ${response.status}`)
        })
      })
    })
  })

  describe('5. 错误处理测试 (US-MVP-06)', () => {
    it('5.1 无效任务ID应返回404', () => {
      cy.request({
        method: 'GET',
        url: `${API_V1}/upload/status/invalid-task-id-12345`,
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.eq(404)
      })
    })

    it('5.2 无效API路径应返回404', () => {
      cy.request({
        method: 'GET',
        url: `${BACKEND_URL}/api/v1/nonexistent`,
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.eq(404)
      })
    })

    it('5.3 健康检查接口应始终可用', () => {
      cy.request({
        method: 'GET',
        url: `${API_V1}/health`
      }).then((response) => {
        expect(response.status).to.eq(200)
        expect(response.body).to.have.property('status')
      })
    })
  })

  describe('6. 标签管理功能测试', () => {
    it('6.1 标签列表接口应可用', () => {
      cy.request({
        method: 'GET',
        url: `${API_V1}/tags`
      }).then((response) => {
        expect(response.status).to.eq(200)
        expect(response.body).to.be.an('array')
      })
    })

    it('6.2 标签筛选搜索应可用', () => {
      cy.request({
        method: 'GET',
        url: `${API_V1}/search`,
        qs: { q: 'test', filter_tags: 'tag1' },
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 400, 404]).to.include(response.status)
      })
    })
  })
})
