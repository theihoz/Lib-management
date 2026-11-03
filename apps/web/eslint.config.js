import js from "@eslint/js";
import jsxA11y from "eslint-plugin-jsx-a11y";
import reactHooks from "eslint-plugin-react-hooks";
import globals from "globals";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist", "coverage", "node_modules", "src/api/schema.d.ts"] },
  {
    files: ["**/*.{ts,tsx}"],
    extends: [js.configs.recommended, ...tseslint.configs.recommendedTypeChecked],
    languageOptions: {
      globals: globals.browser,
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
    plugins: { "react-hooks": reactHooks, "jsx-a11y": jsxA11y },
    rules: {
      ...reactHooks.configs.recommended.rules,
      ...jsxA11y.flatConfigs.recommended.rules,
      // A named overflow region is focusable so tables can be scrolled by keyboard.
      "jsx-a11y/no-noninteractive-tabindex": ["error", { roles: ["region"] }],
      // Network access goes through src/api (spec M0 frontend, section 2).
      "no-restricted-globals": [
        "error",
        { name: "localStorage", message: "Không lưu token/PII vào storage." },
        { name: "sessionStorage", message: "Không lưu token/PII vào storage." },
      ],
    },
  },
  {
    files: ["eslint.config.js"],
    extends: [js.configs.recommended],
    languageOptions: { globals: globals.node },
  },
);
