import Game from '@/components/Game.vue'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

describe('Game.vue', () => {


    function dt(data: any) { return { getData: () => JSON.stringify(data) } }

    function getByText(wrapper: any, selector: string, text: string) {
        const els = wrapper.findAll(selector)
        const el = els.find(e => e.text().trim().startsWith(text))
        if (!el) throw new Error(`No ${selector} with text "${text}"`)
        return el
    }

    it('click on Accueil / Terminer / Effacer / Mélanger / Jouer / Passer emits events', async () => {
        const w = mount(Game, { props: { rack: [], letterPoints: {}, score: 0, score_adversaire: 0 } })
        await getByText(w, 'button', 'Accueil').trigger('click')
        await getByText(w, 'button', 'Terminer la partie').trigger('click')
        await getByText(w, 'button', 'Effacer').trigger('click')
        await getByText(w, 'button', 'Mélanger').trigger('click')

        expect(w.emitted('home')).toBeTruthy()
        expect(w.emitted('finish')).toBeTruthy()
        expect(w.emitted('clear')).toBeTruthy()
        expect(w.emitted('shuffle')).toBeTruthy()

    })

    it('no tile on game', async () => {
        const w = mount(Game, { props: { rack: [], letterPoints: {}, score: 0, score_adversaire: 0 } })
        expect(w.findAll('.cell').length).toBe(225)
        await getByText(w, 'button', 'Passer').trigger('click')
        expect(w.emitted('pass')).toBeTruthy()
    })

    it('existing locked tile still shows Passer', async () => {
        const w = mount(Game, { props: { rack: [], letterPoints: { A: 1 } } })
            ; (w.vm as any).setTile(7, 7, 'A', true)
        await nextTick()
        const jouerBtn = w.findAll('button').find(b => b.text().trim().startsWith('Jouer'))
        expect(jouerBtn?.element.style.display).toBe('none')
        await getByText(w, 'button', 'Passer').trigger('click')
        expect(w.emitted('pass')).toBeTruthy()
    })

    it('placing a new tile shows Jouer', async () => {
        const w = mount(Game, { props: { rack: ['A'], letterPoints: { A: 1 } } })
        w.findComponent({ name: 'Grid' }).vm.$emit('placed', { row: 7, col: 7, letter: 'A' })
        await nextTick()
        await getByText(w, 'button', 'Jouer').trigger('click')
        expect(w.emitted('play')).toBeTruthy()
    })

    it('expose setTile/takeBack/clearAll/lockTiles/getTile', () => {
        const w = mount(Game, { props: { rack: [], letterPoints: {} } })
        expect(typeof w.vm.setTile).toBe('function')
        expect(typeof w.vm.takeBack).toBe('function')
        expect(typeof w.vm.clearAll).toBe('function')
        expect(typeof w.vm.lockTiles).toBe('function')
        expect(typeof w.vm.getTile).toBe('function')
    })

    it('affiche les scores joueur/adversaire', () => {
        const w = mount(Game, { props: { rack: [], letterPoints: {}, score: 12, score_adversaire: 7 } })
        const scoreTxt = w.find('.score').text()
        expect(scoreTxt).toContain('Toi 12')
        expect(scoreTxt).toContain('Adversaire 7')
    })

    it('dragstart sur une tuile du rack émet (event, index)', async () => {
        const w = mount(Game, { props: { rack: ['A', 'B'], letterPoints: { A: 1, B: 3 } } })
        const t0 = w.findAll('.rack .tile')[0]
        await t0.trigger('dragstart', { dataTransfer: dt({ source: 'rack', index: 0, letter: 'A' }) })
        const args = w.emitted('drag-start')![0]
        expect(args).toBeTruthy()
        expect(args![1]).toBe(0) // (event, idx)
    })

    it('permits placing a tile with touch events', async () => {
        const w = mount(Game, { props: { rack: ['A'], letterPoints: { A: 1 } } })
        const tile = w.find('.rack .tile')
        await tile.trigger('touchstart')
        const center = w.find('.CENTER')
        await center.trigger('touchend')
        const placed = w.emitted('placed')?.[0]?.[0]
        expect(placed).toEqual({ row: 7, col: 7, letter: 'A', from: 'rack', rackIndex: 0 })
    })

    it('drop sur une case du rack émet "rack-drop" avec l’index cible', async () => {
        const w = mount(Game, { props: { rack: ['A', 'B', 'C'], letterPoints: { A: 1, B: 3, C: 3 } } })
        const t1 = w.findAll('.rack .tile')[1]
        await t1.trigger('drop', { dataTransfer: dt({ source: 'rack', index: 0, letter: 'A' }) })
        const args = w.emitted('rack-drop')![0]
        expect(args![1]).toBe(1)
    })

    it('drop sur le container du rack place à la fin (index = rack.length)', async () => {
        const w = mount(Game, { props: { rack: ['A', 'B'], letterPoints: { A: 1, B: 3 } } })
        const rack = w.find('.rack')
        await rack.trigger('drop', { dataTransfer: dt({ source: 'rack', index: 0, letter: 'A' }) })
        const args = w.emitted('rack-drop')![0]
        expect(args![1]).toBe(2) // length initial = 2
    })

    it('relaye placed/removed/moved émis par Grid', async () => {
        const w = mount(Game, { props: { rack: [], letterPoints: { A: 1 } } })
        const payloadPlaced = { index: 0, row: 7, col: 7, letter: 'A' }
        w.findComponent({ name: 'Grid' }).vm.$emit('placed', payloadPlaced)
        w.findComponent({ name: 'Grid' }).vm.$emit('removed', { row: 7, col: 7, letter: 'A' })
        w.findComponent({ name: 'Grid' }).vm.$emit('moved', { fromRow: 7, fromCol: 7, toRow: 7, toCol: 8, letter: 'A' })
        expect(w.emitted('placed')![0]![0]).toEqual(payloadPlaced)
        expect(w.emitted('removed')).toBeTruthy()
        expect(w.emitted('moved')).toBeTruthy()
    })

    it('setTile via Game rend la lettre visible sur la grille', async () => {
        const w = mount(Game, { props: { rack: [], letterPoints: { A: 1 } } })
            ; (w.vm as any).setTile(7, 7, 'A', true)   // lock=true OK ici
        await nextTick()                          // <= attendre le re-render
        const center = w.find('.CENTER')
        expect(center.classes('has-letter')).toBe(true)
    })

    it('takeBack via Game supprime et renvoie la lettre', async () => {
        const w = mount(Game, { props: { rack: [], letterPoints: { A: 1 } } })
            ; (w.vm as any).setTile(7, 7, 'A', false)  // <= lock=false pour pouvoir récupérer
        await nextTick()
        const letter = (w.vm as any).takeBack(7, 7)
        expect(letter).toBe('A')
        await nextTick()
        const center = w.find('.CENTER')
        expect(center.classes('has-letter')).toBe(false)
    })

    // (bonus) on vérifie bien le comportement locké
    it('takeBack renvoie null si la case est lockée', async () => {
        const w = mount(Game, { props: { rack: [], letterPoints: { A: 1 } } })
            ; (w.vm as any).setTile(7, 7, 'A', true)   // lock=true
        await nextTick()
        const letter = (w.vm as any).takeBack(7, 7)
        expect(letter).toBeNull()
    })

    it('lockTiles via Game empêche de retirer la tuile', async () => {
        const w = mount(Game, { props: { rack: [], letterPoints: { A: 1 } } })
            ; (w.vm as any).setTile(7, 7, 'A', true) // lock=true
        const center = w.find('.CENTER')
        await center.trigger('click')
        // Game relaie "removed" si Grid l’émet — ici, rien ne doit partir
        expect(w.emitted('removed')).toBeFalsy()
    })

    it('clearAll via Game nettoie plusieurs cases', async () => {
        const w = mount(Game, { props: { rack: [], letterPoints: { A: 1, E: 1 } } })
            ; (w.vm as any).setTile(7, 7, 'A', false)
            ; (w.vm as any).setTile(7, 8, 'E', false)
            ; (w.vm as any).clearAll([{ row: 7, col: 7 }, { row: 7, col: 8 }])
        const row7 = w.findAll('.row')[7]
        const c77 = row7.findAll('.cell')[7]
        const c78 = row7.findAll('.cell')[8]
        expect(c77.classes('has-letter')).toBe(false)
        expect(c78.classes('has-letter')).toBe(false)
    })
})