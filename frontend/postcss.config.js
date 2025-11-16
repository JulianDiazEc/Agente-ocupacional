export default {
  plugins: {
    '@tailwindcss/postcss': {},
    'postcss-preset-env': {
      stage: 2,
      features: {
        'oklab-function': { preserve: false },
        'color-function': { preserve: false },
        'lab-function': { preserve: false },
      },
    },
    autoprefixer: {},
  },
};
