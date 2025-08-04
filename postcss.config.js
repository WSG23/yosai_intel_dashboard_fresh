module.exports = {
  plugins: [
    require('postcss-import'),
    require('tailwindcss-react-native/postcss'),
    require('tailwindcss'),
    require('autoprefixer'),
    process.env.NODE_ENV === 'production' &&
      require('cssnano')({ preset: 'default' }),
    process.env.NODE_ENV === 'production' &&
      require('@fullhuman/postcss-purgecss')({
        content: ['./**/*.py', './**/*.html', './**/*.js', './**/*.tsx'],
        defaultExtractor: content =>
          content.match(/[^\s]*[A-Za-z0-9-_:/]+/g) || []
      })
  ].filter(Boolean)
};
