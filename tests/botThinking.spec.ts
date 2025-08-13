import { ref } from 'vue'
import Popup from '@/components/Popup.vue'
import { mount } from '@vue/test-utils'
import { runBotThinking } from '@/botThinking.js'

describe('Bot thinking popup', () => {
  it('renders loading popup without actions', () => {
    const wrapper = mount(Popup, { props: { popup: { type: 'loading', message: 'Le bot réfléchit' } } })
    expect(wrapper.text()).toContain('Le bot réfléchit')
    expect(wrapper.findAll('button').length).toBe(0)
  })

  it('runBotThinking shows and hides popup', async () => {
    const popup = ref(null)
    const promise = runBotThinking(popup, async () => {})
    expect(popup.value).toEqual({ type: 'loading', message: 'Le bot réfléchit' })
    await promise
    expect(popup.value).toBeNull()
  })
})
