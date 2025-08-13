module.exports = {
  extends: ['stylelint-config-standard'],
  plugins: ['stylelint-order', '@stylistic/stylelint-plugin'],
  rules: {
    'order/properties-alphabetical-order': true,
    'at-rule-no-unknown': [true, { ignoreAtRules: ['tailwind', 'apply', 'variants', 'responsive', 'screen'] }],
    'no-descending-specificity': null,
    'max-nesting-depth': 3,
    'selector-max-specificity': '0,4,0',
    'selector-class-pattern': null
  }
};
