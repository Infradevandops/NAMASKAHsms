export default {
  plugins: {
    'postcss-preset-env': {
      stage: 3,
      features: {
        'nesting-rules': true,
        'custom-properties': true
      }
    },
    cssnano: {
      preset: ['default', {
        discardComments: {
          removeAll: true
        },
        normalizeUnicode: false
      }]
    }
  }
}
