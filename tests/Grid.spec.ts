import Grid from '@/components/Grid.vue'
import { mount } from '@vue/test-utils'


const letterPoints = { A: 1, E: 1 }

function dt(data: any) {
  return { getData: (key: string) => key === 'text/plain' ? JSON.stringify(data) : '' }
}

describe('Grid.vue', () => {
  const letterPoints = { A: 1 }

  it('renders 15x15 grid and center bonus', () => {
    const wrapper = mount(Grid, { props: { letterPoints } })
    expect(wrapper.findAll('.cell').length).toBe(225)
    expect(wrapper.find('.CENTER').exists()).toBe(true)
  })

  it('emits placed and removed events', async () => {
    const wrapper = mount(Grid, { props: { letterPoints } })
    const cell = wrapper.find('.cell')
    const dataTransfer = {
      getData: () => JSON.stringify({ source: 'rack', index: 0, letter: 'A' })
    }
    await cell.trigger('drop', { dataTransfer })
    expect(wrapper.emitted('placed')).toBeTruthy()
    await cell.trigger('click')
    expect(wrapper.emitted('removed')).toBeTruthy()
  })

  it('places tile from rack on center cell and emits complete payload', async () => {
    const wrapper = mount(Grid, { props: { letterPoints } })
    const center = wrapper.find('.CENTER')
    await center.trigger('drop', { dataTransfer: dt({ source: 'rack', index: 0, letter: 'A' }) })
    const placed = wrapper.emitted('placed')?.[0]?.[0]
    expect(placed).toEqual({ row: 7, col: 7, letter: 'A', from: 'rack', rackIndex: 0 })
  })

  it('moves tile from (7,7) to (7,8) and emits "moved" event', async () => {
    const wrapper = mount(Grid, { props: { letterPoints } })
    const center = wrapper.find('.CENTER')
    await center.trigger('drop', { dataTransfer: dt({ source: 'rack', index: 0, letter: 'A' }) })

    const rightCell = wrapper.find('[data-row="7"][data-col="8"]') // adapte si tu as ces data-attrs
    await rightCell.trigger('drop', { dataTransfer: dt({ source: 'board', row: 7, col: 7, letter: 'A' }) })

    const moved = wrapper.emitted('moved')?.[0]?.[0]
    expect(moved).toEqual({ from: { row: 7, col: 7 }, to: { row: 7, col: 8 }, letter: 'A' })
  })

  it('rejects placing on already occupied cell', async () => {
    const wrapper = mount(Grid, { props: { letterPoints } })
    const center = wrapper.find('.CENTER')
    await center.trigger('drop', { dataTransfer: dt({ source: 'rack', index: 0, letter: 'A' }) })
    await center.trigger('drop', { dataTransfer: dt({ source: 'rack', index: 1, letter: 'E' }) })
    expect(wrapper.emitted('placed')?.length).toBe(1) // second drop didn't emit
  })

  it('click on occupied cell emits "removed" with coordinates', async () => {
    const wrapper = mount(Grid, { props: { letterPoints } })
    const center = wrapper.find('.CENTER')
    await center.trigger('drop', { dataTransfer: dt({ source: 'rack', index: 0, letter: 'A' }) })
    await center.trigger('click')
    const removed = wrapper.emitted('removed')?.[0]?.[0]
    expect(removed).toEqual({ row: 7, col: 7, letter: 'A' })
  })

  it('renders bonus classes (TW/DW/TL/DL) at expected positions', () => {
    const w = mount(Grid, { props: { letterPoints } })
    expect(w.findAll('.TW').length).toBeGreaterThan(0)
    expect(w.findAll('.DW').length).toBeGreaterThan(0)
    expect(w.findAll('.TL').length).toBeGreaterThan(0)
    expect(w.findAll('.DL').length).toBeGreaterThan(0)
  })

  it('has specific bonus classes at given coordinates', () => {
    const w = mount(Grid, { props: { letterPoints } })
    expect(w.find('[data-row="0"][data-col="0"]').classes()).toContain('TW')
    expect(w.find('[data-row="1"][data-col="1"]').classes()).toContain('DW')
    expect(w.find('[data-row="1"][data-col="5"]').classes()).toContain('TL')
    expect(w.find('[data-row="0"][data-col="3"]').classes()).toContain('DL')
  })

  it('places a blank tile and indicates blank=true', async () => {
    const wrapper = mount(Grid, { props: { letterPoints } })
    const center = wrapper.find('.CENTER')
    await center.trigger('drop', { dataTransfer: dt({ source: 'rack', index: 0, letter: '*' }) })
    const placed = wrapper.emitted('placed')?.[0]?.[0]
    expect((placed as any).blank).toBe(true)
  })

})




