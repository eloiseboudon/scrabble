import Game from '@/components/Game.vue'
import { mount } from '@vue/test-utils'

describe('Game.vue', () => {
    it('Click Pass emits "pass"', async () => {
        const w = mount(Game, { props: { rack: [], letterPoints: {} } })
        await w.get('button:has-text("Passer")').trigger('click')
        expect(w.emitted('pass')).toBeTruthy()
    })

    it('expose setTile/takeBack/clearAll/lockTiles', () => {
        const w = mount(Game, { props: { rack: [], letterPoints: {} } })
        expect(typeof w.vm.setTile).toBe('function')
        expect(typeof w.vm.takeBack).toBe('function')
        expect(typeof w.vm.clearAll).toBe('function')
        expect(typeof w.vm.lockTiles).toBe('function')
    })
})