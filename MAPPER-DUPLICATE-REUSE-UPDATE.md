# Database Mapper: reusable File B matches

Apply this update to the root of `gds-backoffice`.

What changed:

- Automatic matching explicitly supports many File A rows choosing the same best File B row.
- Those shared File B assignments remain visible in **Step 5 — Resolve duplicate matches**.
- Step 5 now has **Accept all duplicates**, which confirms every currently displayed duplicate group in one action.
- A backend regression test verifies that two File A rows can automatically select the same File B row.

The existing duplicate-value check when configuring fields is unchanged. It checks whether a file itself contains indistinguishable selected-field combinations; it is separate from allowing several File A records to map to one File B record.

After replacing the files, restart the desktop development app. For a distributable installer, rebuild it:

```powershell
npx.cmd --yes pnpm@11.25.0 desktop:build
```
