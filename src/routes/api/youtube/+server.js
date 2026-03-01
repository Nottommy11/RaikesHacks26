import { json } from '@sveltejs/kit';
import { YOUTUBE_API_KEY } from '$lib/config.js';

export async function GET({ url }) {
  const videoUrl = url.searchParams.get('url');
  if (!videoUrl) return json({ error: 'No URL provided' }, { status: 400 });

  // Extract video ID from any YouTube URL format
  const match = videoUrl.match(
    /(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/
  );
  if (!match) return json({ error: 'Could not parse YouTube video ID' }, { status: 400 });

  const videoId = match[1];

  try {
    const res = await fetch(
      `https://www.googleapis.com/youtube/v3/videos?part=snippet&id=${videoId}&key=${YOUTUBE_API_KEY}`
    );
    const data = await res.json();

    if (!data.items?.length) return json({ error: 'Video not found' }, { status: 404 });

    const snippet = data.items[0].snippet;

    // Gather all possible tag signals
    const rawTags    = snippet.tags ?? [];
    const titleWords = snippet.title
      .toLowerCase()
      .replace(/[^a-z0-9 ]/g, ' ')
      .split(/\s+/)
      .filter(w => w.length > 3);
    const descWords  = (snippet.description ?? '')
      .toLowerCase()
      .replace(/[^a-z0-9 ]/g, ' ')
      .split(/\s+/)
      .filter(w => w.length > 4)
      .slice(0, 40);

    return json({
      videoId,
      title:       snippet.title,
      channel:     snippet.channelTitle,
      thumbnail:   snippet.thumbnails?.medium?.url ?? null,
      rawTags:     rawTags.map(t => t.toLowerCase()),
      titleWords,
      descWords,
    });
  } catch (e) {
    return json({ error: 'YouTube API request failed' }, { status: 500 });
  }
}
