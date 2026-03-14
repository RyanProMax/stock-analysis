import path from 'path'

const config = {
  'src/**/*.{ts,tsx,js,jsx}': (filenames) => {
    const relativeFiles = filenames.join(' ')
    return [
      `prettier --write ${relativeFiles}`,
      `eslint --fix ${relativeFiles}`,
    ]
  },
  'src/**/*.{json,css,md}': (filenames) => {
    const relativeFiles = filenames.join(' ')
    return `prettier --write ${relativeFiles}`
  },
}

export default config
