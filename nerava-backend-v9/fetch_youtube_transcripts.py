import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from pytube import YouTube
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)


INPUT_FILE = "videos.txt"
OUTPUT_FILE = "videos_transcripts.txt"


def extract_video_id(url_or_id: str) -> str:
    """
    Accepts either:
      - full YouTube URL (watch, youtu.be, etc.)
      - or a raw video ID
    Returns the video ID string.
    """
    s = url_or_id.strip()
    if not s:
        return ""

    # Already looks like an 11-char ID
    if re.fullmatch(r"[0-9A-Za-z_-]{11}", s):
        return s

    # Try to parse as URL
    try:
        parsed = urlparse(s)
    except Exception:
        return ""

    if "youtube.com" in parsed.netloc:
        qs = parse_qs(parsed.query)
        if "v" in qs and qs["v"]:
            return qs["v"][0]
    elif "youtu.be" in parsed.netloc:
        # e.g. https://youtu.be/<id>
        return parsed.path.lstrip("/")

    return ""


def get_metadata(video_id: str) -> dict:
    """Fetch basic metadata using pytube. Returns None if it fails."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        yt = YouTube(url)
        return {
            "video_id": video_id,
            "url": url,
            "title": yt.title,
            "author": yt.author,
            "length_seconds": yt.length,
            "publish_date": yt.publish_date.isoformat() if yt.publish_date else None,
        }
    except Exception as e:
        # pytube often breaks with YouTube API changes - return minimal metadata
        print(f"    ⚠️  Could not fetch metadata: {e}")
        return {
            "video_id": video_id,
            "url": url,
            "title": "[Metadata unavailable]",
            "author": "[Metadata unavailable]",
            "length_seconds": None,
            "publish_date": None,
        }


def get_transcript_text(video_id: str) -> str:
    """
    Fetch transcript and return as a single string.
    If no transcript is available, returns an empty string.
    """
    try:
        # YouTubeTranscriptApi needs to be instantiated first
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=["en", "en-US"])
        # FetchedTranscript is iterable and contains FetchedTranscriptSnippet objects
        parts = []
        for snippet in fetched:
            text = snippet.text.strip()
            if text:
                parts.append(text.replace("\n", " "))
        return " ".join(parts)
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable, Exception) as e:
        return ""


def main():
    input_path = Path(INPUT_FILE)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    lines = [l.strip() for l in input_path.read_text(encoding="utf-8").splitlines()]
    lines = [l for l in lines if l]  # drop empty lines
    # Strip comments (everything after #) from each line
    lines = [l.split("#")[0].strip() for l in lines]
    lines = [l for l in lines if l]  # drop empty lines again after stripping comments

    out_lines = []
    for idx, line in enumerate(lines, start=1):
        print(f"[{idx}/{len(lines)}] Processing: {line}")

        video_id = extract_video_id(line)
        if not video_id:
            print(f"  ❌ Could not extract video ID, skipping.")
            continue

        # Get metadata (may fail due to YouTube API changes in pytube)
        meta = get_metadata(video_id)
        if not meta:
            print(f"  ⚠️  Could not fetch metadata, continuing with transcript only...")
            meta = {
                "video_id": video_id,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "title": "[Metadata unavailable]",
                "author": "[Metadata unavailable]",
                "length_seconds": None,
                "publish_date": None,
            }

        transcript_text = get_transcript_text(video_id)
        if not transcript_text:
            print("  ⚠ No transcript available.")

        # Write a clearly delimited block for this video
        out_lines.append("=" * 80)
        out_lines.append(f"VIDEO #{idx}")
        out_lines.append("-" * 80)
        out_lines.append(f"Video ID      : {meta['video_id']}")
        out_lines.append(f"URL           : {meta['url']}")
        out_lines.append(f"Title         : {meta['title']}")
        out_lines.append(f"Channel       : {meta['author']}")
        out_lines.append(f"Length (sec)  : {meta['length_seconds']}")
        out_lines.append(f"Publish Date  : {meta['publish_date']}")
        out_lines.append("")
        out_lines.append("TRANSCRIPT:")
        out_lines.append(transcript_text if transcript_text else "[NO TRANSCRIPT AVAILABLE]")
        out_lines.append("")  # extra blank line between videos

    output_path = Path(OUTPUT_FILE)
    output_path.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"\n✅ Done. Output saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
