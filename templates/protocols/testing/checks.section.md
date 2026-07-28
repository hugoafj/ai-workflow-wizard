Before declaring a task done, the agent MUST run and leave green:
\`\`\`bash
npm run lint
npm run build
npm run test        # if there is unit/integration
npm run test -- --coverage  # if coverage targets are active — must meet the configured threshold
npm run test:e2e    # if there is e2e
\`\`\`

Additionally, if E2E specs were generated in this task, **show the user the `--headed`
command with the exact spec path** before declaring done (see the TDD Protocol):
\`\`\`bash
npm run test:e2e -- --headed --workers=1 --project=chromium e2e/<exact-name>.spec.ts
\`\`\`
```
