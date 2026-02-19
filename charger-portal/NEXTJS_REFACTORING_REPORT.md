# Next.js Refactoring Report
## Based on Latest Next.js Documentation Review

**Date**: January 2025  
**Current Version**: Next.js 14.2.5  
**Recommended Version**: Next.js 15.x or 16.x

---

## Executive Summary

This report identifies refactoring opportunities in the charger-portal Next.js application based on the latest Next.js best practices and documentation. The codebase is currently using an older version (14.2.5) and follows patterns that don't leverage Next.js App Router's full capabilities, particularly Server Components and Server Actions.

---

## Critical Issues

### 1. **Version Upgrade Required** ⚠️

**Current**: Next.js 14.2.5  
**Recommended**: Next.js 15.x or 16.x

**Impact**: 
- Missing performance improvements and new features
- Missing React 19 support (Next.js 15+)
- Missing async Dynamic APIs improvements

**Breaking Changes to Consider**:
- In Next.js 15+, `params` and `searchParams` are now async and must be awaited
- `cookies()` and `headers()` are now async APIs

**Action**: Upgrade using the official codemod:
```bash
npx @next/codemod@latest upgrade
```

---

### 2. **Overuse of Client Components** 🔴

**Issue**: The entire `app/page.tsx` is marked as `'use client'`, which means:
- No server-side rendering benefits
- Larger JavaScript bundle sent to client
- Missing automatic static optimization
- No server-side data fetching

**Current Pattern**:
```tsx
// app/page.tsx
'use client'
export default function DashboardPage() {
  const dashboard = useSavingsDashboard() // Client-side hook
  // ...
}
```

**Recommended Pattern**:
```tsx
// app/page.tsx (Server Component)
import { DashboardContent } from './components/dashboard/DashboardContent'

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<{ property?: string; dateRange?: string }>
}) {
  const params = await searchParams
  const dashboard = await getDashboardData(params.property, params.dateRange)
  
  return <DashboardContent initialData={dashboard} />
}
```

**Benefits**:
- Smaller bundle size
- Faster initial page load
- Better SEO
- Automatic caching

---

### 3. **Client-Side Data Fetching Instead of Server Components** 🔴

**Issue**: Using `useSavingsDashboard()` hook with mock data instead of Server Components with async data fetching.

**Current Pattern**:
```tsx
// lib/hooks/useSavingsDashboard.ts
'use client'
export function useSavingsDashboard() {
  const [data, setData] = useState(mockDashboardData)
  // Client-side state management
}
```

**Recommended Pattern**:
```tsx
// lib/data/dashboard.ts (Server-side)
export async function getDashboardData(
  propertyId: string,
  dateRange: DateRangeKey
): Promise<DashboardData> {
  // Fetch from API or database
  const res = await fetch(`${API_URL}/dashboard/${propertyId}?range=${dateRange}`, {
    next: { revalidate: 60 } // Cache for 60 seconds
  })
  return res.json()
}

// app/page.tsx (Server Component)
export default async function DashboardPage() {
  const dashboard = await getDashboardData('standard-domain', 'LAST_30_DAYS')
  return <DashboardContent data={dashboard} />
}
```

**Benefits**:
- Automatic request deduplication
- Built-in caching
- Better performance
- Type-safe data fetching

---

### 4. **Missing Server Actions for Mutations** 🟡

**Issue**: Using client-side state updates (`purchaseNova`, `updateAutoTopUp`) instead of Server Actions.

**Current Pattern**:
```tsx
// lib/hooks/useSavingsDashboard.ts
const purchaseNova = async (amountUsd: number) => {
  setIsLoading(true)
  await new Promise(resolve => setTimeout(resolve, 800))
  // Client-side state update
  setDynamicState(prev => ({ ... }))
}
```

**Recommended Pattern**:
```tsx
// app/actions/dashboard.ts
'use server'

import { revalidatePath } from 'next/cache'

export async function purchaseNova(
  propertyId: string,
  amountUsd: number,
  note?: string
) {
  // Server-side validation
  if (amountUsd <= 0) {
    return { error: 'Amount must be greater than 0' }
  }

  // Call API
  const response = await fetch(`${API_URL}/nova/purchase`, {
    method: 'POST',
    body: JSON.stringify({ propertyId, amountUsd, note }),
  })

  if (!response.ok) {
    return { error: 'Purchase failed' }
  }

  // Revalidate dashboard cache
  revalidatePath('/dashboard')
  
  return { success: true }
}

// app/components/dashboard/BuyNovaDialog.tsx
'use client'
import { purchaseNova } from '@/app/actions/dashboard'

export function BuyNovaDialog({ propertyId }: { propertyId: string }) {
  const handlePurchase = async (amountUsd: number) => {
    const result = await purchaseNova(propertyId, amountUsd)
    if (result.error) {
      // Handle error
    }
  }
}
```

**Benefits**:
- Server-side validation
- Automatic cache revalidation
- Progressive enhancement
- Type-safe mutations

---

### 5. **No Suspense Boundaries** 🟡

**Issue**: Loading states are managed manually with `isLoading` flags instead of using React Suspense.

**Current Pattern**:
```tsx
{dashboard.isLoading ? <LoadingSpinner /> : <KpiCards kpis={dashboard.kpis} />}
```

**Recommended Pattern**:
```tsx
// app/components/dashboard/KpiCardsWrapper.tsx
import { Suspense } from 'react'
import { KpiCards } from './KpiCards'
import { getKPIs } from '@/lib/data/dashboard'

export async function KpiCardsWrapper({ propertyId }: { propertyId: string }) {
  const kpis = await getKPIs(propertyId)
  return <KpiCards kpis={kpis} />
}

// app/page.tsx
<Suspense fallback={<KpiCardsSkeleton />}>
  <KpiCardsWrapper propertyId={selectedProperty.id} />
</Suspense>
```

**Benefits**:
- Streaming SSR
- Better loading UX
- Automatic loading states
- Parallel data fetching

---

### 6. **Layout Component Should Be Server Component** 🟡

**Issue**: `DashboardLayout` is a client component when it could be a Server Component with nested client components.

**Current Pattern**:
```tsx
// app/components/layout/DashboardLayout.tsx
'use client'
export function DashboardLayout({ children }) {
  const dashboard = useSavingsDashboard() // Forces client component
  return <MainShell {...dashboard}>{children}</MainShell>
}
```

**Recommended Pattern**:
```tsx
// app/components/layout/DashboardLayout.tsx (Server Component)
import { MainShell } from './MainShell'
import { getProperties } from '@/lib/data/dashboard'

export async function DashboardLayout({ 
  children,
  selectedPropertyId,
  dateRange 
}: { 
  children: React.ReactNode
  selectedPropertyId: string
  dateRange: DateRangeKey
}) {
  const properties = await getProperties()
  const selectedProperty = properties.find(p => p.id === selectedPropertyId)
  
  return (
    <MainShell
      selectedProperty={selectedProperty}
      properties={properties}
      dateRange={dateRange}
    >
      {children}
    </MainShell>
  )
}

// app/components/layout/MainShell.tsx (Client Component - only for interactivity)
'use client'
export function MainShell({ children, ...props }) {
  // Only interactive parts need 'use client'
  return <div>{children}</div>
}
```

**Benefits**:
- Smaller bundle
- Server-side data fetching in layout
- Better performance

---

### 7. **Missing Caching Strategy** 🟡

**Issue**: No explicit caching configuration for data fetching.

**Recommended Pattern**:
```tsx
// lib/data/dashboard.ts
export async function getDashboardData(propertyId: string) {
  const res = await fetch(`${API_URL}/dashboard/${propertyId}`, {
    next: { 
      revalidate: 60, // Revalidate every 60 seconds
      tags: ['dashboard', `dashboard-${propertyId}`]
    }
  })
  return res.json()
}

// In Server Actions, revalidate specific tags:
import { revalidateTag } from 'next/cache'

export async function purchaseNova(...) {
  // ... purchase logic
  revalidateTag(`dashboard-${propertyId}`)
}
```

**Benefits**:
- Automatic request deduplication
- Configurable cache duration
- Targeted cache invalidation

---

### 8. **Missing Error Boundaries** 🟡

**Issue**: No error handling boundaries for Server Components.

**Recommended Pattern**:
```tsx
// app/dashboard/error.tsx
'use client'
export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div>
      <h2>Something went wrong!</h2>
      <button onClick={() => reset()}>Try again</button>
    </div>
  )
}
```

---

### 9. **Missing Loading States** 🟡

**Issue**: No `loading.tsx` files for route-level loading states.

**Recommended Pattern**:
```tsx
// app/dashboard/loading.tsx
export default function Loading() {
  return <DashboardSkeleton />
}
```

---

## Refactoring Priority

### High Priority 🔴
1. **Upgrade to Next.js 15+** - Required for future compatibility
2. **Convert page.tsx to Server Component** - Major performance improvement
3. **Implement Server-side Data Fetching** - Replace client hooks with async Server Components

### Medium Priority 🟡
4. **Add Server Actions** - Replace client-side mutations
5. **Add Suspense Boundaries** - Better loading UX
6. **Refactor Layout Components** - Optimize component boundaries
7. **Add Caching Strategy** - Improve performance

### Low Priority 🟢
8. **Add Error Boundaries** - Better error handling
9. **Add Loading States** - Better UX
10. **Optimize Component Structure** - Further performance gains

---

## Migration Strategy

### Phase 1: Preparation
1. Upgrade Next.js to 15.x
2. Run codemod for async params (if needed)
3. Update React to 19 (if upgrading to Next.js 15+)

### Phase 2: Data Layer
1. Create server-side data fetching functions
2. Replace mock data with API calls
3. Add caching configuration

### Phase 3: Component Refactoring
1. Convert `page.tsx` to Server Component
2. Extract interactive parts to separate Client Components
3. Refactor `DashboardLayout` to Server Component

### Phase 4: Mutations
1. Create Server Actions for `purchaseNova` and `updateAutoTopUp`
2. Replace client-side state updates
3. Add proper error handling

### Phase 5: Polish
1. Add Suspense boundaries
2. Add error boundaries
3. Add loading states
4. Optimize bundle size

---

## Code Examples

### Example: Refactored Page Component

```tsx
// app/page.tsx (Server Component)
import { Suspense } from 'react'
import { DashboardContent } from './components/dashboard/DashboardContent'
import { DashboardSkeleton } from './components/dashboard/DashboardSkeleton'
import { getDashboardData } from '@/lib/data/dashboard'
import { getProperties } from '@/lib/data/dashboard'

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<{ property?: string; dateRange?: string }>
}) {
  const params = await searchParams
  const propertyId = params.property || 'standard-domain'
  const dateRange = (params.dateRange as DateRangeKey) || 'LAST_30_DAYS'
  
  // Fetch data in parallel
  const [dashboard, properties] = await Promise.all([
    getDashboardData(propertyId, dateRange),
    getProperties(),
  ])

  return (
    <Suspense fallback={<DashboardSkeleton />}>
      <DashboardContent
        initialData={dashboard}
        properties={properties}
        selectedPropertyId={propertyId}
        dateRange={dateRange}
      />
    </Suspense>
  )
}
```

### Example: Server Action

```tsx
// app/actions/dashboard.ts
'use server'

import { revalidatePath, revalidateTag } from 'next/cache'
import { z } from 'zod'

const purchaseNovaSchema = z.object({
  propertyId: z.string(),
  amountUsd: z.number().positive(),
  note: z.string().optional(),
})

export async function purchaseNova(formData: FormData) {
  const rawData = {
    propertyId: formData.get('propertyId'),
    amountUsd: Number(formData.get('amountUsd')),
    note: formData.get('note'),
  }

  const validated = purchaseNovaSchema.safeParse(rawData)
  
  if (!validated.success) {
    return {
      error: 'Invalid input',
      details: validated.error.flatten().fieldErrors,
    }
  }

  try {
    const response = await fetch(`${process.env.API_URL}/nova/purchase`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(validated.data),
    })

    if (!response.ok) {
      return { error: 'Purchase failed' }
    }

    // Revalidate cache
    revalidatePath('/dashboard')
    revalidateTag(`dashboard-${validated.data.propertyId}`)

    return { success: true }
  } catch (error) {
    return { error: 'Network error' }
  }
}
```

---

## Testing Checklist

After refactoring, verify:
- [ ] Page loads correctly
- [ ] Data fetching works
- [ ] Mutations work (purchaseNova, updateAutoTopUp)
- [ ] Loading states display correctly
- [ ] Error states handle gracefully
- [ ] Caching works as expected
- [ ] Bundle size is reduced
- [ ] Performance metrics improved

---

## Resources

- [Next.js 15 Upgrade Guide](https://nextjs.org/docs/app/building-your-application/upgrading/version-15)
- [Server Components Documentation](https://nextjs.org/docs/app/building-your-application/rendering/server-components)
- [Server Actions Documentation](https://nextjs.org/docs/app/building-your-application/data-fetching/server-actions-and-mutations)
- [Data Fetching Best Practices](https://nextjs.org/docs/app/building-your-application/data-fetching/fetching-caching-and-revalidating)
- [Caching Documentation](https://nextjs.org/docs/app/building-your-application/caching)

---

## Conclusion

The charger-portal application would benefit significantly from adopting Next.js App Router best practices, particularly:
- Server Components for data fetching
- Server Actions for mutations
- Proper component boundaries
- Caching strategies

These changes will improve performance, reduce bundle size, and provide a better developer experience.












