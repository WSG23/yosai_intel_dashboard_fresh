module.exports = {
  plugins: [
    require('postcss-import'),
    require('autoprefixer'),
    process.env.NODE_ENV === 'production' &&
      require('cssnano')({ preset: 'default' }),
    process.env.NODE_ENV === 'production' &&
      require('@fullhuman/postcss-purgecss').default({
        content: ['./**/*.py', './**/*.html', './**/*.js'],
        defaultExtractor: content => content.match(/[^\s]*[A-Za-z0-9-_:/]+/g) || []
      })
  ].filter(Boolean)
};
