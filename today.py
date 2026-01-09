#!/usr/bin/env python3
"""
GitHub Profile Stats Updater
Fetches GitHub statistics and generates ASCII art from profile picture.
"""

import os
import re
import requests
from io import BytesIO

# Configuration
GITHUB_TOKEN = os.environ.get("GH_TOKEN")
GITHUB_USERNAME = "roniel-rhack"
SVG_FILES = ["dark_mode.svg", "light_mode.svg"]

# ASCII characters from dark to light
ASCII_CHARS = " ░▒▓█"

# GraphQL query for GitHub stats
GRAPHQL_QUERY = """
query($login: String!) {
  user(login: $login) {
    avatarUrl
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes {
        stargazerCount
      }
    }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
    }
    followers {
      totalCount
    }
  }
}
"""


def fetch_github_data():
    """Fetch GitHub statistics and avatar URL using GraphQL API."""
    if not GITHUB_TOKEN:
        print("Warning: GH_TOKEN not set. Using placeholder values.")
        return None

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": GRAPHQL_QUERY, "variables": {"login": GITHUB_USERNAME}},
        headers=headers
    )

    if response.status_code != 200:
        print(f"Error fetching data: {response.status_code}")
        return None

    data = response.json()

    if "errors" in data:
        print(f"GraphQL errors: {data['errors']}")
        return None

    return data["data"]["user"]


def image_to_ascii(image_url, width=42, height=26):
    """Convert image from URL to ASCII art."""
    try:
        from PIL import Image
    except ImportError:
        print("Pillow not installed, using placeholder ASCII art")
        return None

    # Download image
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))

    # Convert to grayscale
    img = img.convert('L')

    # Resize with aspect ratio correction for monospace fonts
    aspect_ratio = img.height / img.width
    new_height = int(width * aspect_ratio * 0.55)
    new_height = min(new_height, height)

    img = img.resize((width, new_height), Image.Resampling.LANCZOS)

    # Convert pixels to ASCII characters
    pixels = list(img.getdata())
    ascii_lines = []

    for i in range(0, len(pixels), width):
        row = pixels[i:i + width]
        line = ""
        for pixel in row:
            # Invert: dark pixels become filled blocks, light pixels become spaces
            char_idx = int((255 - pixel) / 255 * (len(ASCII_CHARS) - 1))
            line += ASCII_CHARS[char_idx]
        ascii_lines.append(line)

    return ascii_lines


def generate_ascii_svg_element(ascii_lines, x=50, start_y=55, line_height=11):
    """Generate SVG text element with ASCII art."""
    tspans = []
    for i, line in enumerate(ascii_lines):
        dy = 0 if i == 0 else line_height
        # Escape special XML characters
        escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        tspans.append(f'    <tspan x="{x}" dy="{dy}">{escaped}</tspan>')

    return "\n".join(tspans)


def update_svg(filename, stats, ascii_svg_content):
    """Update SVG file with GitHub statistics and ASCII art."""
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()

    # Update stats
    replacements = {
        "repos": (r'(<tspan class="stat-value" id="repos">).*?(</tspan>)',
                  rf'\g<1>{stats["repos"]}\g<2>'),
        "commits": (r'(<tspan class="stat-value" id="commits">).*?(</tspan>)',
                    rf'\g<1>{stats["commits"]}\g<2>'),
        "stars": (r'(<tspan class="stat-value" id="stars">).*?(</tspan>)',
                  rf'\g<1>{stats["stars"]}\g<2>'),
        "followers": (r'(<tspan class="stat-value" id="followers">).*?(</tspan>)',
                      rf'\g<1>{stats["followers"]}\g<2>')
    }

    for stat_name, (pattern, replacement) in replacements.items():
        content = re.sub(pattern, replacement, content)

    # Update ASCII art if provided
    if ascii_svg_content:
        # Pattern to match the ASCII art text element
        ascii_pattern = r'(<text x="30" y="55" class="ascii-art ascii">)\s*.*?\s*(</text>)'
        ascii_replacement = rf'\g<1>\n{ascii_svg_content}\n  \g<2>'
        content = re.sub(ascii_pattern, ascii_replacement, content, flags=re.DOTALL)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Updated {filename}")


def main():
    """Main entry point."""
    print(f"Fetching GitHub data for {GITHUB_USERNAME}...")

    user_data = fetch_github_data()

    if not user_data:
        print("Failed to fetch GitHub data")
        exit(1)

    # Extract stats
    repos = user_data["repositories"]
    contributions = user_data["contributionsCollection"]
    total_stars = sum(repo["stargazerCount"] for repo in repos["nodes"])
    total_commits = (
        contributions["totalCommitContributions"] +
        contributions["restrictedContributionsCount"]
    )

    stats = {
        "repos": str(repos["totalCount"]),
        "commits": f"{total_commits:,}",
        "stars": str(total_stars),
        "followers": str(user_data["followers"]["totalCount"])
    }

    print(f"Stats: {stats}")

    # Generate ASCII art from avatar
    avatar_url = user_data["avatarUrl"]
    print(f"Generating ASCII art from: {avatar_url}")

    ascii_lines = image_to_ascii(avatar_url)
    ascii_svg_content = None

    if ascii_lines:
        ascii_svg_content = generate_ascii_svg_element(ascii_lines)
        print(f"Generated ASCII art with {len(ascii_lines)} lines")

    # Update SVG files
    for svg_file in SVG_FILES:
        if os.path.exists(svg_file):
            update_svg(svg_file, stats, ascii_svg_content)
        else:
            print(f"Warning: {svg_file} not found")

    print("Done!")


if __name__ == "__main__":
    main()
