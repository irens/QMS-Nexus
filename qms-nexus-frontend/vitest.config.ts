// 测试配置文件
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/**',
        'src/test/**',
        '**/*.d.ts',
        '**/*.config.ts',
        '**/*.config.js',
        '**/mock/**',
        '**/mocks/**'
      ],
      include: [
        'src/**/*.{ts,vue}',
        '!src/**/*.test.{ts,vue}',
        '!src/**/*.spec.{ts,vue}'
      ],
      thresholds: {
        lines: 85,
        functions: 85,
        branches: 85,
        statements: 85
      }
    },
    include: [
      'src/**/*.{test,spec}.{ts,vue}'
    ],
    exclude: [
      'node_modules/**',
      'dist/**',
      'coverage/**'
    ]
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
      '~': resolve(__dirname, './src')
    }
  }
})