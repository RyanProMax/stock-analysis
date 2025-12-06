const path = require('path')

module.exports = {
  'web/**/*.{ts,tsx,js,jsx}': (filenames) => {
    const relativeFiles = filenames.map((f) => path.relative('web', f)).join(' ')
    return [
      `sh -c "cd web && prettier --write ${relativeFiles}"`,
      `sh -c "cd web && eslint --fix ${relativeFiles}"`,
    ]
  },
  'web/**/*.{json,css,md}': (filenames) => {
    const relativeFiles = filenames.map((f) => path.relative('web', f)).join(' ')
    return `sh -c "cd web && prettier --write ${relativeFiles}"`
  },
  'server/**/*.py': (filenames) => {
    const relativeFiles = filenames.map((f) => path.relative('server', f)).join(' ')
    return `sh -c "cd server && poetry run black --line-length 100 ${relativeFiles}"`
  },
}

