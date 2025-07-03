module.exports = {
  plugins: [
    require('postcss-import'),
    require('autoprefixer'),
    require('cssnano')({ preset: 'default' }),
    process.env.NODE_ENV === 'production' &&
      require('@fullhuman/postcss-purgecss')({
        content: ['./**/*.py', './**/*.html', './**/*.js'],
        defaultExtractor: content => content.match(/[^\s]*[A-Za-z0-9-_:/]+/g) || []
      })
  ].filter(Boolean)
};
