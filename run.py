#!/usr/bin/env python3

# This is a small script to use data already generated in data/ to
# create plots that break down repositories by external and internal
# contributors.

import os
import json
from jinja2 import Template

here = os.path.abspath(os.path.dirname(__file__))


def read_json(filename):
    with open(filename, "r") as fd:
        content = json.loads(fd.read())
    return content


# internal and external users file
internal_users = read_json(os.path.join(here, "data", "intUsers.json"))
ext_users = read_json(os.path.join(here, "data", "extUsers.json"))

# Keep counts of repositories by internal/external
repos = {}


def update_users(data, key="internal"):
    """Given a dictionary of data, update repos with user counts."""
    for user, meta in data["data"].items():
        if "contributedLabRepositories" in meta:
            for repo in meta["contributedLabRepositories"].get("nodes", []):
                if repo not in repos:
                    repos[repo] = {"external": 0, "internal": 0}
                repos[repo][key] += 1


update_users(internal_users, "internal")
update_users(ext_users, "external")

# Keep track of maxes
max_external = 0
max_internal = 0
max_total = 0

# Calculate a total
for repo, counts in repos.items():
    counts["total"] = counts["internal"] + counts["external"]

    # Update max counts
    if counts["external"] > max_external:
        max_external = counts["external"]

    if counts["internal"] > max_internal:
        max_internal = counts["internal"]

    if counts["total"] > max_total:
        max_total = counts["total"]

# Sort data based on number of total
repos = {
    k: v
    for k, v in sorted(repos.items(), reverse=True, key=lambda item: item[1]["total"])
}

# Filter down to those with less than 100
filtered = {}
for repo, meta in repos.items():
    if meta["total"] <= 100:
        filtered[repo] = meta

filtered = {
    k: v
    for k, v in sorted(
        filtered.items(), reverse=True, key=lambda item: item[1]["total"]
    )
}
internal_sorted = {
    k: v
    for k, v in sorted(
        filtered.items(), reverse=True, key=lambda item: item[1]["internal"]
    )
}
external_sorted = {
    k: v
    for k, v in sorted(
        filtered.items(), reverse=True, key=lambda item: item[1]["external"]
    )
}


def count_ranges(repos, metric="total"):
    # Count ranges - we will make custom because they are so uneven
    ranges = {
        "0-10": 0,
        "10-20": 0,
        "20-30": 0,
        "30-50": 0,
        "50-100": 0,
        "100-200": 0,
        "200+": 0,
    }
    for key, count in ranges.items():
        if "+" not in key:
            start, end = key.split("-")
        else:
            start = key.strip("+")
            end = 10000000
        start = int(start)
        end = int(end)

        # Now add repos
        for repo, meta in repos.items():
            if meta[metric] >= start and meta[metric] < end:
                ranges[key] += 1
    return ranges


total_ranges = count_ranges(repos, "total")
external_ranges = count_ranges(repos, "external")
internal_ranges = count_ranges(repos, "internal")

ranges = {
    "total": total_ranges,
    "external": external_ranges,
    "internal": internal_ranges,
}

# Write to template
with open("template.html", "r") as fd:
    template = Template(fd.read())

keys = ["external", "total", "internal"]
result = template.render(
    repos=repos,
    filtered=filtered,
    keys=keys,
    ranges=ranges,
    internal=internal_sorted,
    external=external_sorted,
)
with open("index.html", "w") as fd:
    fd.write(result)
