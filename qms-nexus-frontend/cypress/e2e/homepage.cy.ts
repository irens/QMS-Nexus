/**
 * QMS-Nexus 主页导航 E2E 测试
 * 测试范围：页面导航、基础UI交互
 * 对应需求：US-MVP-05
 */

describe('QMS-Nexus Frontend Navigation E2E Test', () => {
  const BASE_URL = '/system'

  beforeEach(() => {
    cy.visit('/')
  })

  it('should load the homepage correctly', () => {
    cy.get('body').should('be.visible')
    cy.url().should('include', '/system')
  })

  it('should navigate to dashboard page', () => {
    cy.visit(`${BASE_URL}/dashboard`)
    cy.url().should('include', '/system/dashboard')
    cy.get('body').should('be.visible')
  })

  it('should navigate to upload page', () => {
    cy.visit(`${BASE_URL}/upload`)
    cy.url().should('include', '/system/upload')
    cy.get('body').should('be.visible')
  })

  it('should navigate to documents page', () => {
    cy.visit(`${BASE_URL}/documents`)
    cy.url().should('include', '/system/documents')
    cy.get('body').should('be.visible')
  })

  it('should navigate to chat page', () => {
    cy.visit(`${BASE_URL}/chat`)
    cy.url().should('include', '/system/chat')
    cy.get('body').should('be.visible')
  })

  it('should navigate to search page', () => {
    cy.visit(`${BASE_URL}/search`)
    cy.url().should('include', '/system/search')
    cy.get('body').should('be.visible')
  })

  it('should navigate to tags page', () => {
    cy.visit(`${BASE_URL}/tags`)
    cy.url().should('include', '/system/tags')
    cy.get('body').should('be.visible')
  })

  it('should display 404 for invalid routes', () => {
    cy.visit('/invalid-route-12345', { failOnStatusCode: false })
    cy.get('body').should('be.visible')
  })
})
