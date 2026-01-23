# feat: Mobile Optimization for Autography

## Overview

Make Autography beautiful and fully functional on mobile devices (iOS Safari, Android Chrome). The current implementation has desktop-first patterns with several critical mobile blockers.

## Problem Statement

The app has **partial mobile support** but critical issues block usability:
- Hover-only interactions (citations, clip buttons) don't work on touch devices
- Missing viewport configuration causes zoom issues
- Small touch targets (<44px) frustrate users
- Fixed-width elements overflow on small screens

## Acceptance Criteria

### Critical (Blocks Mobile Use)
- [ ] Add viewport meta tag with `viewport-fit: cover`
- [ ] Replace hover-triggered citation previews with tap/click
- [ ] Show clip action buttons always on mobile (not hover-only)
- [ ] Make citation popup width responsive (not fixed `w-72`)

### High Priority (Major UX)
- [ ] Increase all touch targets to ≥44px minimum
- [ ] Fix follow-up input width on mobile (remove complex calc)
- [ ] Reduce left margin (`ml-11`) on small screens
- [ ] Make SourceCard collapse button always visible on mobile

### Medium Priority (Polish)
- [ ] Increase small font sizes (9-11px → 12-13px minimum)
- [ ] Add safe-area padding for notched devices (`pb-safe`)
- [ ] Test and fix drawer behavior on mobile keyboards

## Technical Approach

### 1. Viewport Configuration
**File:** `web/app/layout.tsx`

```tsx
import { Viewport } from 'next';

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
};
```

### 2. Citation Preview - Touch Support
**File:** `web/components/AnswerDisplay.tsx:32-77`

Current: `onMouseEnter`/`onMouseLeave` only
Fix: Add `onClick` toggle + tap-outside-to-close

```tsx
// Replace hover handlers with click/tap
const [activePreview, setActivePreview] = useState<number | null>(null);

// Toggle on click
onClick={() => setActivePreview(activePreview === idx ? null : idx)}

// Close on outside click
useEffect(() => {
  const handleClickOutside = () => setActivePreview(null);
  document.addEventListener('click', handleClickOutside);
  return () => document.removeEventListener('click', handleClickOutside);
}, []);
```

### 3. Clip Drawer Actions - Always Visible on Mobile
**File:** `web/app/page.tsx:879-898`

Current: `opacity-0 group-hover:opacity-100`
Fix: `opacity-100 md:opacity-0 md:group-hover:opacity-100`

### 4. Touch Target Sizes
Minimum 44x44px for all interactive elements:

| Component | Current | Fix |
|-----------|---------|-----|
| SourceCard collapse | `w-5 h-5` | `w-8 h-8 md:w-5 md:h-5` |
| Citation badge | `min-w-[1.25rem]` | `min-w-[2rem] min-h-[2rem]` on mobile |
| Clip action buttons | `w-6 h-6` | `w-10 h-10 md:w-6 md:h-6` |

### 5. Responsive Layout Adjustments
**File:** `web/app/page.tsx`

```tsx
// Current (line 636)
<div className="... ml-11 mt-3">

// Fix: Reduce margin on mobile
<div className="... ml-4 md:ml-11 mt-3">

// Current follow-up input (line 758)
<div className="relative max-w-[calc(100%-14rem-1.5rem)] lg:max-w-none lg:mr-[15.5rem]">

// Fix: Full width on mobile
<div className="relative w-full lg:max-w-none lg:mr-[15.5rem]">
```

### 6. Safe Area Support
Install plugin and add to fixed elements:

```bash
npm install tailwindcss-safe-area
```

```tsx
// Clips drawer
<div className="fixed bottom-0 ... pb-safe">

// Input form (when at bottom)
<form className="... pb-safe">
```

### 7. Font Size Increases
**File:** `web/app/page.tsx`

| Current | Location | New |
|---------|----------|-----|
| `text-[9px]` | Badge labels | `text-[11px]` |
| `text-[10px]` | Source headers, author | `text-xs` (12px) |
| `text-[11px]` | Source content | `text-xs` (12px) |

## Files to Modify

| File | Changes |
|------|---------|
| `web/app/layout.tsx` | Add viewport export |
| `web/app/page.tsx` | Layout margins, touch targets, clip buttons, font sizes |
| `web/components/AnswerDisplay.tsx` | Click-based citation preview |
| `web/tailwind.config.js` | Add safe-area plugin |
| `web/app/globals.css` | Add `font-size: 16px` to inputs (prevent iOS zoom) |

## Testing Checklist

- [ ] iPhone Safari (portrait + landscape)
- [ ] iPhone with notch (safe areas)
- [ ] Android Chrome
- [ ] iPad (tablet breakpoint)
- [ ] Test with keyboard open (input positioning)
- [ ] Test citation tap → preview → tap outside to close
- [ ] Test clip drawer swipe and actions
- [ ] Verify all text readable without zooming

## Success Metrics

- All interactive elements have ≥44px touch targets
- No horizontal scroll on any mobile viewport
- Citation previews work on first tap
- Clip buttons discoverable without hover
- Text readable at arm's length (no <12px body text)
