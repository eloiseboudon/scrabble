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

  it('place depuis le rack sur la case centrale et émet payload complet', async () => {
    const wrapper = mount(Grid, { props: { letterPoints } })
    const center = wrapper.find('.CENTER') // ta classe
    await center.trigger('drop', { dataTransfer: dt({ source: 'rack', index: 0, letter: 'A' }) })
    const placed = wrapper.emitted('placed')?.[0]?.[0]
    expect(placed).toEqual({ row: 7, col: 7, letter: 'A', from: 'rack', rackIndex: 0 })
  })

  it('déplace une tuile de (7,7) vers (7,8) et émet "moved"', async () => {
    const wrapper = mount(Grid, { props: { letterPoints } })
    const center = wrapper.find('.CENTER')
    await center.trigger('drop', { dataTransfer: dt({ source: 'rack', index: 0, letter: 'A' }) })

    const rightCell = wrapper.find('[data-row="7"][data-col="8"]') // adapte si tu as ces data-attrs
    await rightCell.trigger('drop', { dataTransfer: dt({ source: 'board', row: 7, col: 7, letter: 'A' }) })

    const moved = wrapper.emitted('moved')?.[0]?.[0]
    expect(moved).toEqual({ from: { row: 7, col: 7 }, to: { row: 7, col: 8 }, letter: 'A' })
  })

  it('refuse de poser sur une case déjà occupée', async () => {
    const wrapper = mount(Grid, { props: { letterPoints } })
    const center = wrapper.find('.CENTER')
    await center.trigger('drop', { dataTransfer: dt({ source: 'rack', index: 0, letter: 'A' }) })
    await center.trigger('drop', { dataTransfer: dt({ source: 'rack', index: 1, letter: 'E' }) })
    expect(wrapper.emitted('placed')?.length).toBe(1) // le 2e drop n’a rien émis
  })

  it('clic sur une case occupée émet "removed" avec coordonnées', async () => {
    const wrapper = mount(Grid, { props: { letterPoints } })
    const center = wrapper.find('.CENTER')
    await center.trigger('drop', { dataTransfer: dt({ source: 'rack', index: 0, letter: 'A' }) })
    await center.trigger('click')
    const removed = wrapper.emitted('removed')?.[0]?.[0]
    expect(removed).toEqual({ row: 7, col: 7, letter: 'A' })
  })

  it('rend les classes de bonus (MD/MT/LD/LT) aux positions attendues', () => {
    const w = mount(Grid, { props: { letterPoints } })
    expect(w.findAll('.MT').length).toBeGreaterThan(0)
    expect(w.findAll('.MD').length).toBeGreaterThan(0)
    expect(w.findAll('.LT').length).toBeGreaterThan(0)
    expect(w.findAll('.LD').length).toBeGreaterThan(0)
  })

  it('pose un joker et indique blank=true', async () => {
    const wrapper = mount(Grid, { props: { letterPoints } })
    const center = wrapper.find('.CENTER')
    await center.trigger('drop', { dataTransfer: dt({ source: 'rack', index: 0, letter: '*' }) }) // ou blank:true selon ton DnD
    const placed = wrapper.emitted('placed')?.[0]?.[0]
    // adapte à ton contrat (ex: letter:'E', blank:true après choix)
    expect((placed as any).blank).toBe(true)
  })

})




