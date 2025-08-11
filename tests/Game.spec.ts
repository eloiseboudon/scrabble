import Game from '@/components/Game.vue'
import { mount } from '@vue/test-utils'

describe('Game.vue', () => {

    function dt(data: any) { return { getData: () => JSON.stringify(data) } }

    it('click on Accueil / Terminer / Effacer / Mélanger / Jouer / Passer emits events', async () => {
        const w = mount(Game, { props: { rack: [], letterPoints: {}, score: 0, score_adversaire: 0 } })

        const button_pass = w.findAll('button').find(b => b.text() === 'Passer')
        expect(button_pass).toBeTruthy()
        await button_pass!.trigger('click')

        const button_play = w.findAll('button').find(b => b.text() === 'Jouer')
        expect(button_play).toBeTruthy()
        await button_play!.trigger('click')

        const button_shuffle = w.findAll('button').find(b => b.text() === 'Mélanger')
        expect(button_shuffle).toBeTruthy()
        await button_shuffle!.trigger('click')

        const button_clear = w.findAll('button').find(b => b.text() === 'Effacer')
        expect(button_clear).toBeTruthy()
        await button_clear!.trigger('click')

        const button_home = w.findAll('button').find(b => b.text() === 'Accueil')
        expect(button_home).toBeTruthy()
        await button_home!.trigger('click')

        const button_finish = w.findAll('button').find(b => b.text() === 'Terminer la partie')
        expect(button_finish).toBeTruthy()
        await button_finish!.trigger('click')

        expect(w.emitted('home')).toBeTruthy()
        expect(w.emitted('finish')).toBeTruthy()
        expect(w.emitted('clear')).toBeTruthy()
        expect(w.emitted('shuffle')).toBeTruthy()
        expect(w.emitted('play')).toBeTruthy()
        expect(w.emitted('pass')).toBeTruthy()
    })





    await w.get('button:has-text("Accueil")').trigger('click')
    await w.get('button:has-text("Terminer la partie")').trigger('click')
    await w.get('button:has-text("Effacer")').trigger('click')
    await w.get('button:has-text("Mélanger")').trigger('click')
    await w.get('button:has-text("Jouer")').trigger('click')
    await w.get('button:has-text("Passer")').trigger('click')
    expect(w.emitted('home')).toBeTruthy()
    expect(w.emitted('finish')).toBeTruthy()
    expect(w.emitted('clear')).toBeTruthy()
    expect(w.emitted('shuffle')).toBeTruthy()
    expect(w.emitted('play')).toBeTruthy()
    expect(w.emitted('pass')).toBeTruthy()
})

it('expose setTile/takeBack/clearAll/lockTiles', () => {
    const w = mount(Game, { props: { rack: [], letterPoints: {} } })
    expect(typeof w.vm.setTile).toBe('function')
    expect(typeof w.vm.takeBack).toBe('function')
    expect(typeof w.vm.clearAll).toBe('function')
    expect(typeof w.vm.lockTiles).toBe('function')
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
    await t0.trigger('dragstart', { dataTransfer: new DataTransfer() })
    const args = w.emitted('drag-start')![0]
    expect(args).toBeTruthy()
    expect(args![1]).toBe(0) // (event, idx)
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
        ; (w.vm as any).setTile(7, 7, 'A', false)
    // on cherche la case centrale rendue par Grid
    const center = w.find('.CENTER')
    expect(center.classes('has-letter')).toBe(true)
})

it('takeBack via Game supprime et renvoie la lettre', async () => {
    const w = mount(Game, { props: { rack: [], letterPoints: { A: 1 } } })
        ; (w.vm as any).setTile(7, 7, 'A', false)
    const letter = (w.vm as any).takeBack(7, 7)
    expect(letter).toBe('A')
    const center = w.find('.CENTER')
    expect(center.classes('has-letter')).toBe(false)
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