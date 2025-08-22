import { http, HttpResponse } from 'msw'
import { API_BASE } from '../../frontend/public/api.js'

export const handlers = [
  http.post('/games', () => HttpResponse.json({ game_id: 'g1' })),
  http.post('/games/g1/join', () => HttpResponse.json({ player_id: 'p1' })),
  http.post('/games/g1/start', () => HttpResponse.json({ ok: true })),
  http.post(`${API_BASE}/auth/login`, async ({ request }) => {
    const { username } = await request.json()
    if (username === 'good') {
      return HttpResponse.json({ user_id: 'u1' })
    }
    return HttpResponse.json({ detail: 'Bad credentials' }, { status: 400 })
  }),
  http.post(`${API_BASE}/auth/register`, () =>
    HttpResponse.json({ user_id: 'u2' })
  ),
]
