import tailwindcss from '@tailwindcss/postcss'
import autoprefixer from 'autoprefixer'

const config = {
  plugins: [
    tailwindcss({
      base: process.cwd(),
    }),
    autoprefixer,
  ],
}

export default config
