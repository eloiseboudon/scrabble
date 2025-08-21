import { server } from './msw/server'
import { afterAll, afterEach, beforeAll } from 'vitest'
import * as Vue from 'vue'

// Expose Vue globally for components relying on global Vue reference
(globalThis as any).Vue = Vue

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
