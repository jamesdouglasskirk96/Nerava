const imageCache = new Map<string, string>()

export function getCachedImage(url: string): string | null {
  return imageCache.get(url) || null
}

export function setCachedImage(url: string): void {
  if (!imageCache.has(url)) {
    imageCache.set(url, url)
  }
}

export function preloadImage(url: string): Promise<void> {
  return new Promise((resolve, reject) => {
    if (imageCache.has(url)) {
      resolve()
      return
    }
    const img = new Image()
    img.onload = () => {
      setCachedImage(url)
      resolve()
    }
    img.onerror = reject
    img.src = url
  })
}




