export default [
  {
    ignores: ["node_modules/**", "dist/**"],
    rules: {
      semi: "error",
      quotes: ["error", "single"],
      eqeqeq: "error",
      "no-console": "warn",
    },
  },
  {
    files: ["**/*.{js,jsx}"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    plugins: {
      prettier: (await import("eslint-plugin-prettier")).default,
      react: (await import("eslint-plugin-react")).default,
    },
    rules: {
      "prettier/prettier": "error",
      "react/no-danger": "error",
    },
    settings: {
      react: {
        version: "detect",
      },
    },
  },
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      parser: (await import("@typescript-eslint/parser")).default,
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    plugins: {
      "@typescript-eslint": (await import("@typescript-eslint/eslint-plugin")).default,
      prettier: (await import("eslint-plugin-prettier")).default,
      react: (await import("eslint-plugin-react")).default,
    },
    rules: {
      "prettier/prettier": "error",
      "react/no-danger": "error",
    },
    settings: {
      react: {
        version: "detect",
      },
    },
  },
];
