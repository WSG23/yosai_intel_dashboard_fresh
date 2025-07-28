export default [
  {
    files: ["**/*.{ts,tsx}"],
    ignores: ["node_modules/**"],
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
      "@typescript-eslint": (await import("@typescript-eslint/eslint-plugin"))
        .default,
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
