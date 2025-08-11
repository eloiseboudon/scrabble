import { http, HttpResponse } from 'msw'

export const handlers = [
  http.post('/games', () => HttpResponse.json({ game_id: 'g1' })),
  http.post('/games/g1/join', () => HttpResponse.json({ player_id: 'p1' })),
  http.post('/games/g1/start', () => HttpResponse.json({ ok: true })),
]
