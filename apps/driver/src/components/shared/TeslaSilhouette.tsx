/** Map Tesla exterior_color API value to CSS colors (body + darker shade) */
export function getTeslaColors(color?: string | null): { body: string; dark: string } {
  if (!color) return { body: '#C0C0C0', dark: '#999' }
  const c = color.toLowerCase().replace(/[\s_-]/g, '')
  if (c.includes('white') || c.includes('pearl')) return { body: '#E8E8E8', dark: '#D0D0D0' }
  if (c.includes('black') || c.includes('obsidian')) return { body: '#2A2A2A', dark: '#111' }
  if (c.includes('red') || c.includes('cherry') || c.includes('ultra')) return { body: '#A82428', dark: '#7A1A1D' }
  if (c.includes('blue')) return { body: '#2E4F7A', dark: '#1E3555' }
  if (c.includes('stealth')) return { body: '#5A5E63', dark: '#3E4145' }
  if (c.includes('midnight') || c.includes('silver') || c.includes('quicksilver')) return { body: '#71767B', dark: '#555' }
  if (c.includes('gray') || c.includes('grey')) return { body: '#6B6E73', dark: '#4A4D51' }
  if (c.includes('green')) return { body: '#2D5E3E', dark: '#1E4029' }
  return { body: '#C0C0C0', dark: '#999' }
}

/** Get a clean model name (just "Model 3", not year or trim) */
export function getCleanModelName(model?: string): string {
  if (!model) return 'Tesla'
  const match = model.match(/(Model\s*[3SYXC]|Cybertruck|Roadster)/i)
  if (match) return match[1]
  return model
}

/** Tesla vehicle silhouette — side profile view */
export function TeslaSilhouette({ color, model }: { color: { body: string; dark: string }; model?: string }) {
  const m = getCleanModelName(model).toLowerCase()
  const isSUV = m.includes('y') || m.includes('x') || m.includes('cybertruck')

  return (
    <svg viewBox="0 0 200 80" className="w-full h-full" fill="none">
      <defs>
        <linearGradient id="bodyGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color.body} />
          <stop offset="100%" stopColor={color.dark} />
        </linearGradient>
        <linearGradient id="windowGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#B8D4E8" />
          <stop offset="100%" stopColor="#7EACC8" />
        </linearGradient>
      </defs>

      {isSUV ? (
        // SUV (Model Y / X) — taller, more upright rear
        <>
          {/* Body */}
          <path d="M22 58 L22 52 C22 50 24 44 32 36 C38 30 52 22 64 20 C76 18 120 17 140 18 C156 19 170 24 176 34 C180 40 182 48 182 54 L182 58 Z" fill="url(#bodyGrad)" />
          {/* Roof highlight */}
          <path d="M40 34 C48 26 60 22 70 20 C82 18 120 17 138 18 C148 19 156 22 160 26" stroke="rgba(255,255,255,0.15)" strokeWidth="1" fill="none" />
          {/* Rear window */}
          <path d="M38 36 C42 30 50 26 58 24 L68 22 L60 36 Z" fill="url(#windowGrad)" rx="2" />
          {/* Front window */}
          <path d="M78 20 C92 18 118 17 134 18 C144 19 154 22 160 28 L148 32 C140 30 120 24 80 24 Z" fill="url(#windowGrad)" />
          {/* Window divider */}
          <line x1="68" y1="22" x2="62" y2="36" stroke={color.dark} strokeWidth="2" />
          <line x1="78" y1="21" x2="76" y2="35" stroke={color.dark} strokeWidth="2" />
          {/* Door handle */}
          <rect x="96" y="34" width="12" height="2" rx="1" fill="rgba(255,255,255,0.2)" />
          {/* Headlight */}
          <ellipse cx="174" cy="40" rx="4" ry="3" fill="#F0F0F0" opacity="0.9" />
          {/* Taillight */}
          <rect x="22" y="42" width="3" height="8" rx="1.5" fill="#CC2222" opacity="0.8" />
          {/* Wheels */}
          <circle cx="52" cy="58" r="12" fill="#222" />
          <circle cx="52" cy="58" r="9" fill="#444" />
          <circle cx="52" cy="58" r="4" fill="#666" />
          <circle cx="156" cy="58" r="12" fill="#222" />
          <circle cx="156" cy="58" r="9" fill="#444" />
          <circle cx="156" cy="58" r="4" fill="#666" />
        </>
      ) : (
        // Sedan (Model 3 / S) — lower, sleeker
        <>
          {/* Body */}
          <path d="M18 58 L18 52 C18 48 22 42 30 34 C38 26 56 20 68 18 C82 16 124 16 144 17 C160 18 172 24 178 36 C181 42 183 50 183 54 L183 58 Z" fill="url(#bodyGrad)" />
          {/* Roof highlight */}
          <path d="M38 32 C46 24 62 20 72 18 C84 16 124 16 142 17 C152 18 162 22 168 28" stroke="rgba(255,255,255,0.15)" strokeWidth="1" fill="none" />
          {/* Rear window */}
          <path d="M36 34 C42 27 52 22 62 20 L72 18 L58 34 Z" fill="url(#windowGrad)" />
          {/* Front window */}
          <path d="M82 17 C96 16 124 16 140 17 C152 18 162 22 168 30 L152 32 C144 28 124 22 84 22 Z" fill="url(#windowGrad)" />
          {/* Window divider */}
          <line x1="72" y1="18" x2="62" y2="34" stroke={color.dark} strokeWidth="2" />
          <line x1="82" y1="18" x2="78" y2="33" stroke={color.dark} strokeWidth="2" />
          {/* Door handle */}
          <rect x="100" y="32" width="12" height="2" rx="1" fill="rgba(255,255,255,0.2)" />
          {/* Headlight */}
          <ellipse cx="178" cy="42" rx="3" ry="3" fill="#F0F0F0" opacity="0.9" />
          {/* Taillight */}
          <rect x="18" y="42" width="3" height="7" rx="1.5" fill="#CC2222" opacity="0.8" />
          {/* Wheels */}
          <circle cx="50" cy="58" r="12" fill="#222" />
          <circle cx="50" cy="58" r="9" fill="#444" />
          <circle cx="50" cy="58" r="4" fill="#666" />
          <circle cx="158" cy="58" r="12" fill="#222" />
          <circle cx="158" cy="58" r="9" fill="#444" />
          <circle cx="158" cy="58" r="4" fill="#666" />
        </>
      )}
    </svg>
  )
}
