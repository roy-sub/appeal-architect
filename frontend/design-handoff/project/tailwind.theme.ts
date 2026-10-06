// Appeal Architect — Tailwind theme extension.
// Values mirror tokens.css exactly. Light only; dark mode removed by request.

import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./app/**/*.{ts,tsx,mdx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ground:         'var(--ground)',        // #F2EDE4
        surface:        'var(--surface)',       // #FFFCF7
        'surface-sunk': 'var(--surface-sunk)',  // #EAE2D6
        ink: {
          DEFAULT: 'var(--ink)',                // #1C1A17
          muted:   'var(--ink-muted)',          // #5E5850
        },
        rule:   'var(--rule)',                  // #DED5C6
        stripe: 'var(--stripe)',                // #D2C8B8

        forest: {
          DEFAULT: 'var(--forest)',             // #14453A
          deep:    'var(--forest-deep)',        // #0E332B
          tint:    'var(--forest-tint)',        // #DCE8E0
        },
        clay: {
          DEFAULT: 'var(--clay)',               // #C85A33
          soft:    'var(--clay-soft)',          // #F7DDCE
          deep:    'var(--clay-deep)',          // #9E4323
        },
        sky: {
          DEFAULT: 'var(--sky)',                // #2F5E78
          tint:    'var(--sky-tint)',           // #DCE7EE
        },
        wheat: 'var(--wheat)',                  // #F2D9A8
        plum:  'var(--plum)',                   // #6B3A5B

        time: {
          DEFAULT:     'var(--time)',             // #A9640F
          ample:       'var(--time-ample)',       // #5E5850
          approaching: 'var(--time-approaching)', // #B8822C
          near:        'var(--time-near)',        // #A9640F
          imminent:    'var(--time-imminent)',    // #8A4409
          track:       'var(--time-track)',       // #E6D7BE
        },
        standing: {
          DEFAULT: 'var(--standing)',           // #14453A
          tint:    'var(--standing-tint)',      // #DCE8E0
        },
        defeated: 'var(--defeated)',            // #837C72
        band: {
          DEFAULT: 'var(--band)',               // #14332C
          ink:     'var(--band-ink)',           // #F4EFE5
          muted:   'var(--band-muted)',         // #A9BDB2
          rule:    'var(--band-rule)',          // #2A4C43
        },
      },
      fontFamily: {
        sans: ['IBM Plex Sans', 'system-ui', 'sans-serif'],
        doc:  ['Newsreader', 'Georgia', 'serif'],
        mono: ['IBM Plex Mono', 'ui-monospace', 'monospace'],
      },
      fontSize: {
        'display-xl': ['76px', { lineHeight: '76px', letterSpacing: '-0.03em', fontWeight: '600' }],
        'display-l':  ['56px', { lineHeight: '60px', letterSpacing: '-0.025em', fontWeight: '600' }],
        'heading-1':  ['44px', { lineHeight: '52px', letterSpacing: '-0.025em', fontWeight: '600' }],
        'heading-2':  ['28px', { lineHeight: '36px', letterSpacing: '-0.015em', fontWeight: '600' }],
        'heading-3':  ['22px', { lineHeight: '30px', letterSpacing: '-0.012em', fontWeight: '600' }],
        'body-l':     ['19px', { lineHeight: '32px' }],
        body:         ['16px', { lineHeight: '26px' }],
        'body-s':     ['14px', { lineHeight: '21px' }],
        doc:          ['18px', { lineHeight: '31px' }],
        mono:         ['13px', { lineHeight: '20px', letterSpacing: '0.01em' }],
        'mono-s':     ['11px', { lineHeight: '16px', letterSpacing: '0.14em' }],
        'numeral-xl': ['104px', { lineHeight: '92px', letterSpacing: '-0.04em', fontWeight: '600' }],
      },
      spacing: {
        1: '4px', 2: '8px', 3: '12px', 4: '16px', 5: '24px', 6: '32px',
        7: '48px', 8: '64px', 9: '96px', 10: '128px', 11: '160px',
      },
      borderRadius: {
        sharp: '2px', sm: '6px', md: '10px', lg: '16px', xl: '24px',
      },
      boxShadow: {
        e1: 'var(--e1)', e2: 'var(--e2)', e3: 'var(--e3)',
      },
      transitionTimingFunction: {
        exit:  'cubic-bezier(.4, 0, 1, 1)',
        enter: 'cubic-bezier(.16, .84, .32, 1)',
        move:  'cubic-bezier(.65, 0, .35, 1)',
      },
      transitionDuration: {
        1: '120ms', 2: '180ms', 3: '260ms', 4: '420ms', 5: '700ms',
      },
    },
  },
}

export default config
