import { rest } from 'msw'

export const handlers = [
  rest.post('/games', (_req, res, ctx) => res(ctx.json({ game_id: 'g1' }))),
  rest.post('/games/g1/join', (_req, res, ctx) => res(ctx.json({ player_id: 'p1' }))),
  rest.post('/games/g1/start', (_req, res, ctx) => res(ctx.json({ ok: true }))),
]
