import Login from '@/components/Login.vue'
import { mount } from '@vue/test-utils'


describe('Login.vue', () => {

    function getByText(wrapper: any, selector: string, text: string) {
        const els = wrapper.findAll(selector)
        const el = els.find(e => e.text().trim() === text)
        if (!el) throw new Error(`No ${selector} with text "${text}"`)
        return el
    }

    it('renders login form', () => {
        const wrapper = mount(Login)
        expect(wrapper.find('form').exists()).toBe(true)
    })

    it('user connect', async () => {
        const wrapper = mount(Login)
        wrapper.find('input').setValue('test')
        await getByText(wrapper, 'button', 'Se connecter').trigger('click')

        expect(wrapper.emitted('auth')).toBeTruthy()
    })

    it('user not connect', () => {
        const wrapper = mount(Login)
        wrapper.find('input').setValue('test')
        wrapper.find('button').trigger('click')
        expect(wrapper.emitted('auth')).toBeFalsy()
    })
})