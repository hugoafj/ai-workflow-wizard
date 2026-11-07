# Testing profiles

<!--
  SINGLE SOURCE of the per-framework testing data. Read by the Builder
  (builder-core.py: AGENTS.md Testing Approach and command descriptions;
  builder-heavy.py: unit/e2e config generation) and by phase46 / phase8
  (menu, packages, scripts). Adding a framework = one entry in "profiles"
  (plus its config template when it needs one); no phase or builder edit.

  Framework -> profile mapping lives in wf-init/lib/state-helpers.sh
  (wf_profile_for_framework). The profile name is stored in state.testing.profile.
  A null or unknown profile resolves to "default" (react), the behavior every
  Node project had before profiles existed.
-->

## Fields

- `runner` / `environment`: what the wizard installs when the project has no runner.
  `null` means the wizard does not pick one (the user decides in phase 4.6).
- `ui`: the stack renders UI, so Testing Library style tests and the `data-testid`
  convention apply.
- `e2e`: `offer` shows the Playwright layer in phase 4.6, `off` hides it (API stacks).
- `unit_config`: key into `unit_configs`; `null` means the wizard writes no unit config.
  `unit_config_by_runner` is the fallback keyed by the runner the user chose.
- `setup_file`: a file the unit config points to (`setupFiles`), staged next to it as
  `{template, target}`. `null` means the profile's config references none. The Builder never
  stages it over a file the project already has, because phase 8 promotes with `rsync -a`,
  which overwrites.
- `ecosystem`: the package manager the profile installs with. Absent means `npm` (every Node
  profile); `php` means Composer, and then `packages` are `composer require --dev` requirements.
- `packages` / `scripts`: installed in phase 8 (8.1c) and set in `package.json` (8.1e)
  only when the wizard owns the runner (`state.testing.runner_existing` is not true). A `php`
  profile has no `scripts`: the wizard never edits `composer.json` scripts, it documents `test_command`.
- `test_command`: the command that runs the unit and integration tests, documented in AGENTS.md
  and used by the checks before declaring a task done. Absent means the `test` script of
  `package.json` (`npm test`); the `php` profiles set it because they have no such script.
- `dummy_test_import`: first line of the placeholder test phase 8 writes when the project
  has no tests yet (empty when the runner provides globals).
- `dummy_test_suffix`: file suffix of that placeholder test (`.spec.ts` for Nest, whose Jest
  config only finds `*.spec.ts`); `null` means phase 8 writes none (Angular generates its own specs).
- `unit_convention` / `integration_convention`: bullets for AGENTS.md Testing Approach.
- `unit_config_frontend` / `setup_file_frontend` / `frontend_extra_packages`: optional, only for the
  profiles a PHP project can use for its frontend (react, next, vue). When `state.testing.layers` has
  `frontend`, the Builder writes the config named by `unit_config_frontend` (scoped to
  `state.testing.frontend_root` and `tests/js`, with JSX allowed in `.js` for React) instead of
  `unit_config`, stages `setup_file_frontend`, and phase 8 installs `packages` plus
  `frontend_extra_packages` with npm. They never apply to a Node project, whose `unit_config` is used.
- `layout_dirs` / `layout_fallback`: optional. When the project has NONE of the `layout_dirs`
  (a non-standard layout), the conventions come from the profile named in `layout_fallback`, which
  says "follow the layout the project already uses" instead of naming folders that do not exist.
- `dev_command` / `dev_port`: Playwright `webServer` values when they differ from the
  Vite defaults of the base template (`npm run dev`, 5173); `null` keeps the template.

```json
{
  "default": "react",
  "profiles": {
    "react": {
      "label": "React (Vitest + Testing Library)",
      "runner": "vitest",
      "environment": "jsdom",
      "ui": true,
      "e2e": "offer",
      "unit_config": "vitest-react",
      "unit_config_by_runner": {},
      "setup_file": {"template": "setup.tmpl.md", "target": "src/test/setup.ts"},
      "packages": ["vitest", "@testing-library/react", "@testing-library/user-event", "@testing-library/jest-dom", "@testing-library/dom", "jsdom", "@vitest/ui", "@vitest/coverage-v8", "@vitejs/plugin-react"],
      "scripts": {"test": "vitest", "test:ui": "vitest --ui", "test:coverage": "vitest run --coverage"},
      "dummy_test_import": "import { describe, it, expect } from 'vitest'",
      "dummy_test_suffix": ".test.ts",
      "unit_convention": "one test file next to the code it covers (`Component.test.tsx` next to the component).",
      "integration_convention": "real render tests in `src/__tests__/integration/` (`*.integration.test.tsx`).",
      "dev_command": null,
      "dev_port": null,
      "unit_config_frontend": "vitest-frontend",
      "setup_file_frontend": {"template": "setup.tmpl.md", "target": "tests/js/setup.ts"},
      "frontend_extra_packages": ["vite"]
    },
    "next": {
      "label": "Next.js (Vitest + Testing Library)",
      "runner": "vitest",
      "environment": "jsdom",
      "ui": true,
      "e2e": "offer",
      "unit_config": "vitest-react",
      "unit_config_by_runner": {},
      "setup_file": {"template": "setup.tmpl.md", "target": "src/test/setup.ts"},
      "packages": ["vitest", "@testing-library/react", "@testing-library/user-event", "@testing-library/jest-dom", "@testing-library/dom", "jsdom", "@vitest/ui", "@vitest/coverage-v8", "@vitejs/plugin-react"],
      "scripts": {"test": "vitest", "test:ui": "vitest --ui", "test:coverage": "vitest run --coverage"},
      "dummy_test_import": "import { describe, it, expect } from 'vitest'",
      "dummy_test_suffix": ".test.ts",
      "unit_convention": "one test file next to the code it covers (`Component.test.tsx` next to the component).",
      "integration_convention": "real render tests in `src/__tests__/integration/` (`*.integration.test.tsx`).",
      "dev_command": null,
      "dev_port": 3000,
      "unit_config_frontend": "vitest-frontend",
      "setup_file_frontend": {"template": "setup.tmpl.md", "target": "tests/js/setup.ts"},
      "frontend_extra_packages": ["vite"]
    },
    "vue": {
      "label": "Vue / Nuxt (Vitest + Vue Test Utils)",
      "runner": "vitest",
      "environment": "jsdom",
      "ui": true,
      "e2e": "offer",
      "unit_config": "vitest-vue",
      "unit_config_by_runner": {},
      "setup_file": null,
      "packages": ["vitest", "@vue/test-utils", "jsdom", "@vitest/ui", "@vitest/coverage-v8", "@vitejs/plugin-vue"],
      "scripts": {"test": "vitest", "test:ui": "vitest --ui", "test:coverage": "vitest run --coverage"},
      "dummy_test_import": "import { describe, it, expect } from 'vitest'",
      "dummy_test_suffix": ".test.ts",
      "unit_convention": "one test file next to the code it covers (`Component.test.ts` next to the component).",
      "integration_convention": "mounted-component tests in `src/__tests__/integration/` (`*.integration.test.ts`).",
      "dev_command": null,
      "dev_port": null,
      "unit_config_frontend": "vitest-frontend-vue",
      "setup_file_frontend": null,
      "frontend_extra_packages": ["vite"]
    },
    "node-api": {
      "label": "Node API: Express, Fastify, Hono, Koa (Vitest + supertest)",
      "runner": "vitest",
      "environment": "node",
      "ui": false,
      "e2e": "off",
      "unit_config": "vitest-node",
      "unit_config_by_runner": {},
      "setup_file": null,
      "packages": ["vitest", "supertest", "@types/supertest", "@vitest/ui", "@vitest/coverage-v8"],
      "scripts": {"test": "vitest", "test:ui": "vitest --ui", "test:coverage": "vitest run --coverage"},
      "dummy_test_import": "import { describe, it, expect } from 'vitest'",
      "dummy_test_suffix": ".test.ts",
      "unit_convention": "one test file next to the module it covers (`users.service.test.ts` next to `users.service.ts`).",
      "integration_convention": "HTTP-level tests with supertest in `test/integration/` (`*.integration.test.ts`).",
      "dev_command": "npm run dev",
      "dev_port": 3000
    },
    "nest": {
      "label": "NestJS (Jest + supertest)",
      "runner": "jest",
      "environment": "node",
      "ui": false,
      "e2e": "off",
      "unit_config": "jest-nest",
      "unit_config_by_runner": {},
      "setup_file": null,
      "packages": ["jest", "ts-jest", "@types/jest", "@nestjs/testing", "supertest", "@types/supertest"],
      "scripts": {"test": "jest", "test:watch": "jest --watch", "test:coverage": "jest --coverage"},
      "dummy_test_import": "",
      "dummy_test_suffix": ".spec.ts",
      "unit_convention": "one `*.spec.ts` next to the provider, controller or pipe it covers (`users.service.spec.ts` next to `users.service.ts`), built with `@nestjs/testing`.",
      "integration_convention": "supertest tests against the Nest app in `test/` (`*.e2e-spec.ts`).",
      "dev_command": "npm run start:dev",
      "dev_port": 3000
    },
    "angular": {
      "label": "Angular (the project's native runner)",
      "runner": null,
      "environment": null,
      "ui": true,
      "e2e": "offer",
      "unit_config": null,
      "unit_config_by_runner": {},
      "setup_file": null,
      "packages": [],
      "scripts": {},
      "dummy_test_import": "",
      "dummy_test_suffix": null,
      "unit_convention": "one `*.spec.ts` next to the component, service or pipe it covers (`app.component.spec.ts` next to `app.component.ts`).",
      "integration_convention": "`TestBed` tests that render a component with its real child components, in the same `*.spec.ts` file or an `*.integration.spec.ts` beside it.",
      "dev_command": "npm start",
      "dev_port": 4200
    },
    "laravel": {
      "label": "Laravel (PHPUnit or Pest)",
      "ecosystem": "php",
      "runner": "phpunit",
      "environment": null,
      "ui": false,
      "e2e": "off",
      "unit_config": null,
      "unit_config_by_runner": {},
      "setup_file": null,
      "packages": ["phpunit/phpunit"],
      "scripts": {},
      "test_command": "php artisan test",
      "dummy_test_import": "",
      "dummy_test_suffix": null,
      "layout_dirs": ["tests/Unit", "tests/Feature"],
      "layout_fallback": "php",
      "unit_convention": "unit tests in `tests/Unit/` (`UserServiceTest.php` for `UserService.php`) for logic that does not need the framework booted.",
      "integration_convention": "feature tests in `tests/Feature/` (`*Test.php`) that boot the app and exercise routes, controllers and the database (use `RefreshDatabase`).",
      "dev_command": null,
      "dev_port": null
    },
    "php": {
      "label": "Other PHP project (PHPUnit)",
      "ecosystem": "php",
      "runner": "phpunit",
      "environment": null,
      "ui": false,
      "e2e": "off",
      "unit_config": null,
      "unit_config_by_runner": {},
      "setup_file": null,
      "packages": ["phpunit/phpunit"],
      "scripts": {},
      "test_command": "vendor/bin/phpunit",
      "dummy_test_import": "",
      "dummy_test_suffix": null,
      "unit_convention": "one test class per class under test in `tests/` (`FooTest.php` for `Foo.php`), following the layout the project already uses.",
      "integration_convention": "tests that exercise several classes together, in the folder the project already uses for them.",
      "dev_command": null,
      "dev_port": null
    },
    "generic": {
      "label": "Other Node project (you choose the runner)",
      "runner": null,
      "environment": null,
      "ui": false,
      "e2e": "offer",
      "unit_config": null,
      "unit_config_by_runner": {"vitest": "vitest-node"},
      "setup_file": null,
      "packages": ["vitest", "@vitest/ui", "@vitest/coverage-v8"],
      "scripts": {"test": "vitest", "test:ui": "vitest --ui", "test:coverage": "vitest run --coverage"},
      "dummy_test_import": "import { describe, it, expect } from 'vitest'",
      "dummy_test_suffix": ".test.ts",
      "unit_convention": "one test file next to the code it covers, following the naming the project already uses.",
      "integration_convention": "tests that exercise several modules together, in the folder the project already uses for them.",
      "dev_command": null,
      "dev_port": null
    }
  },
  "unit_configs": {
    "vitest-react": {"template": "vitest.config.tmpl.md", "target": "vitest.config.ts", "coverage": "coverage-thresholds.tmpl.md", "marker": "test: {\n", "indent": 4},
    "vitest-vue": {"template": "vitest.vue.config.tmpl.md", "target": "vitest.config.ts", "coverage": "coverage-thresholds.tmpl.md", "marker": "test: {\n", "indent": 4},
    "vitest-frontend": {"template": "vitest.frontend.config.tmpl.md", "target": "vitest.config.ts", "coverage": "coverage-thresholds.tmpl.md", "marker": "test: {\n", "indent": 4},
    "vitest-frontend-vue": {"template": "vitest.frontend.vue.config.tmpl.md", "target": "vitest.config.ts", "coverage": "coverage-thresholds.tmpl.md", "marker": "test: {\n", "indent": 4},
    "vitest-node": {"template": "vitest.node.config.tmpl.md", "target": "vitest.config.ts", "coverage": "coverage-thresholds.tmpl.md", "marker": "test: {\n", "indent": 4},
    "jest-nest": {"template": "jest.config.nest.tmpl.md", "target": "jest.config.js", "coverage": "coverage-thresholds.jest.tmpl.md", "marker": "module.exports = {\n", "indent": 2}
  }
}
```
