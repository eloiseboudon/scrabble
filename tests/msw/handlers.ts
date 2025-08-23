import { http, HttpResponse } from 'msw'
export const handlers = [
  http.post('/games', () => HttpResponse.json({ game_id: 'g1' })),
  http.post('/games/g1/join', () => HttpResponse.json({ player_id: 'p1' })),
  http.post('/games/g1/start', () => HttpResponse.json({ ok: true })),
  http.post('http://localhost:8000/auth/login', async ({ request }) => {
    const { username } = await request.json()
    if (username === 'good') {
      return HttpResponse.json({ user_id: 'u1' })
    }
    return HttpResponse.json({ detail: 'Bad credentials' }, { status: 400 })
  }),
  http.post('http://localhost:8000/auth/register', () =>
    HttpResponse.json({ user_id: 'u2' })
  ),
]
