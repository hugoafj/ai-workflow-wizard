# e2e/pages/HomePage.ts — minimal Page Object Model scaffold

Staged when the Page Object Model extra (phase 4.6b, extra 3) is active.
This is the PATTERN, not your real pages: replace the example locators with
real `data-testid` values from your components as features are implemented
(grep `src/` for them — never invent testid values). One class per screen;
specs never hold raw selectors.

```typescript
import { type Locator, type Page, expect } from '@playwright/test'

/**
 * Minimal Page Object example. Real selectors come from each screen's
 * data-testid attributes — grep src/ for them instead of inventing values.
 */
export class HomePage {
  readonly page: Page
  readonly heading: Locator

  constructor(page: Page) {
    this.page = page
    // TODO: replace with a real data-testid from your component, e.g.
    // page.getByTestId('app-title')
    this.heading = page.getByRole('heading', { level: 1 })
  }

  async open(path = '/'): Promise<void> {
    await this.page.goto(path)
    await expect(this.page).toHaveTitle(/.*/)
  }
}
```
