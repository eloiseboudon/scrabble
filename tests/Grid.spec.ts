import { mount } from '@vue/test-utils'
import Grid from '@/components/Grid.vue'

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
})
