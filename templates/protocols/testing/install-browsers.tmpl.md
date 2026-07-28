**Install Playwright browsers** (after `npm install`):

```bash
npx playwright install --with-deps chromium
```

This command downloads the browser. It only needs to be run once per machine. If the user is in CI, the CI workflow also needs this command.
