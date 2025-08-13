import Login from '@/components/Login.vue'
import { mount, flushPromises } from '@vue/test-utils'

describe('Login.vue', () => {
  function getByText(wrapper: any, selector: string, text: string) {
    const els = wrapper.findAll(selector)
    const el = els.find((e: any) => e.text().trim() === text)
    if (!el) throw new Error(`No ${selector} with text "${text}"`)
    return el
  }

  it('renders login form', () => {
    const wrapper = mount(Login)
    expect(wrapper.find('form').exists()).toBe(true)
  })

  it('emits auth on successful login', async () => {
    const wrapper = mount(Login)
    const [user, pass] = wrapper.findAll('input')
    await user.setValue('good')
    await pass.setValue('secret')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(wrapper.emitted('auth')?.[0]?.[0]).toBe('u1')
  })

  it('shows error on failed login', async () => {
    const wrapper = mount(Login)
    const [user, pass] = wrapper.findAll('input')
    await user.setValue('bad')
    await pass.setValue('secret')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(wrapper.emitted('auth')).toBeFalsy()
    const err = wrapper.find('.auth-error')
    expect(err.exists()).toBe(true)
    expect(err.text()).toBe('Bad credentials')
  })

  it('toggles between login and register and clears error', async () => {
    const wrapper = mount(Login)
    const [user, pass] = wrapper.findAll('input')

    // produce an error in login mode
    await user.setValue('bad')
    await pass.setValue('secret')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(wrapper.find('.auth-error').exists()).toBe(true)

    // toggle to register
    await wrapper.find('a').trigger('click')
    expect(wrapper.find('h2').text()).toBe('Inscription')
    expect(wrapper.find('.auth-error').exists()).toBe(false)

    // submit register successfully
    await user.setValue('newuser')
    await pass.setValue('secret')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(wrapper.emitted('auth')?.[0]?.[0]).toBe('u2')
  })

  it('shows error when submitting empty fields', async () => {
    const wrapper = mount(Login)
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(wrapper.emitted('auth')).toBeFalsy()
    const err = wrapper.find('.auth-error')
    expect(err.exists()).toBe(true)
  })
})

