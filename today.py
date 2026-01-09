#!/usr/bin/env python3
"""
GitHub Profile Stats Updater
Fetches GitHub statistics and updates SVG files.
"""

import os
import re
import requests

# Configuration
GITHUB_TOKEN = os.environ.get("GH_TOKEN")
GITHUB_USERNAME = "roniel-rhack"
SVG_FILES = ["dark_mode.svg", "light_mode.svg"]

# GraphQL query for GitHub stats
GRAPHQL_QUERY = """
query($login: String!) {
  user(login: $login) {
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
    """Fetch GitHub statistics using GraphQL API."""
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


def update_svg(filename, stats):
    """Update SVG file with GitHub statistics."""
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

    # Update SVG files
    for svg_file in SVG_FILES:
        if os.path.exists(svg_file):
            update_svg(svg_file, stats)
        else:
            print(f"Warning: {svg_file} not found")

    print("Done!")


if __name__ == "__main__":
    main()
