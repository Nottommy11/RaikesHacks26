import { json } from '@sveltejs/kit';

export async function GET({ url }) {
  const target = url.searchParams.get('url');
  if (!target) return json({ error: 'No URL provided' }, { status: 400 });

  try {
    const res = await fetch(target, {
      headers: { 'User-Agent': 'Mozilla/5.0 (compatible; 1984ButGood/1.0)' },
      signal: AbortSignal.timeout(8000),
    });
    if (!res.ok) return json({ error: `Could not fetch URL (${res.status})` }, { status: 400 });

    const html = await res.text();

    // Extract meta tags
    const getMeta = (name) => {
      const m = html.match(
        new RegExp(`<meta[^>]+(?:name|property)=["']${name}["'][^>]+content=["']([^"']+)["']`, 'i')
      ) || html.match(
        new RegExp(`<meta[^>]+content=["']([^"']+)["'][^>]+(?:name|property)=["']${name}["']`, 'i')
      );
      return m?.[1] ?? null;
    };

    const title       = html.match(/<title[^>]*>([^<]+)<\/title>/i)?.[1]?.trim() ?? '';
    const keywords    = getMeta('keywords') ?? '';
    const description = getMeta('description') ?? getMeta('og:description') ?? '';
    const ogTitle     = getMeta('og:title') ?? '';
    const article     = getMeta('article:tag') ?? '';

    // Parse keyword string into array
    const fromKeywords = keywords
      .split(/[,;|]/)
      .map(k => k.trim().toLowerCase())
      .filter(k => k.length > 2 && k.length < 40);

    // Pull words from title + description
    const fromText = `${ogTitle} ${title} ${description} ${article}`
      .toLowerCase()
      .replace(/[^a-z0-9 ]/g, ' ')
      .split(/\s+/)
      .filter(w => w.length > 4)
      .slice(0, 60);

    // Extract section/category links (common patterns)
    const categoryMatches = [...html.matchAll(/(?:category|tag|topic|section)\/([a-z0-9-]+)/gi)]
      .map(m => m[1].replace(/-/g, ' '))
      .slice(0, 10);

    return json({
      title:      ogTitle || title,
      keywords:   fromKeywords,
      textWords:  fromText,
      categories: categoryMatches,
    });
  } catch (e) {
    return json({ error: `Failed to scrape: ${e.message}` }, { status: 500 });
  }
}
