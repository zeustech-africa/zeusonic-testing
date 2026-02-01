import '../styles/globals.css'

export const parameters = {
  actions: { argTypesRegex: '^on[A-Z].*' },
  backgrounds: {
    default: 'dark',
    values: [
      { name: 'dark', value: '#0F1115' },
      { name: 'surface', value: '#141619' },
    ],
  },
  layout: 'padded',
}

export const decorators = [Story => <div className="min-h-screen p-6 bg-base"><Story /></div>]
