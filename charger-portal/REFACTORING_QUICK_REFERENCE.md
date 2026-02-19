# Next.js Refactoring Quick Reference

## Key Findings Summary

### 🔴 Critical Issues

1. **Version**: Next.js 14.2.5 → Should upgrade to 15.x
2. **Page Component**: Entire `app/page.tsx` is client component → Should be Server Component
3. **Data Fetching**: Using client hooks with mock data → Should use async Server Components

### 🟡 Important Improvements

4. **Mutations**: Client-side state updates → Should use Server Actions
5. **Loading**: Manual `isLoading` flags → Should use Suspense boundaries
6. **Layout**: `DashboardLayout` is client → Should be Server Component with nested clients
7. **Caching**: No caching strategy → Should add `next.revalidate` and cache tags

---

## Quick Wins

### 1. Convert Page to Server Component
```tsx
// Before: app/page.tsx
'use client'
export default function DashboardPage() {
  const dashboard = useSavingsDashboard()
  // ...
}

// After: app/page.tsx
export default async function DashboardPage() {
  const dashboard = await getDashboardData()
  return <DashboardContent data={dashboard} />
}
```

### 2. Create Server Actions
```tsx
// app/actions/dashboard.ts
'use server'
export async function purchaseNova(formData: FormData) {
  // Server-side logic
  revalidatePath('/dashboard')
}
```

### 3. Add Suspense
```tsx
<Suspense fallback={<Skeleton />}>
  <DashboardContent />
</Suspense>
```

---

## Files That Need Refactoring

1. `app/page.tsx` - Convert to Server Component
2. `app/components/layout/DashboardLayout.tsx` - Convert to Server Component
3. `lib/hooks/useSavingsDashboard.ts` - Replace with server-side data fetching
4. `app/components/dashboard/BuyNovaDialog.tsx` - Use Server Actions
5. `app/components/dashboard/NovaBudgetPanel.tsx` - Use Server Actions

---

## Migration Steps

1. **Upgrade**: `npx @next/codemod@latest upgrade`
2. **Create data layer**: `lib/data/dashboard.ts` with async functions
3. **Create actions**: `app/actions/dashboard.ts` with Server Actions
4. **Refactor page**: Convert to Server Component
5. **Add Suspense**: Wrap data-fetching components
6. **Test**: Verify all functionality works

---

See `NEXTJS_REFACTORING_REPORT.md` for detailed analysis and examples.












