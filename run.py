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


def write_json(filename, obj):
    with open(filename, "w") as fd:
        fd.write(json.dumps(obj, indent=4))


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

# Calculate percentages
count_internal_more = 0
count_external_more = 0
count_equal = 0
count_fewer_10 = 0
for name, counts in repos.items():
    if counts["external"] > counts["internal"]:
        count_external_more += 1
    elif counts["external"] < counts["internal"]:
        count_internal_more += 1
    else:
        count_equal += 1

    # less than 10% external?
    if (
        counts["external"] == 0
        or (counts["internal"] / counts["external"]) / len(repos) < 0.1
    ):
        count_fewer_10 += 1


# Calculate a few final metrics!
summary = {
    "total_repos": len(repos),
    # percentage of repos with more internal than external collabs
    "percent_internal_more": round(count_internal_more / len(repos), 2) * 100,
    # percentage of repos with equal contributors of both types
    "percent_equal": round(count_equal / len(repos), 2) * 100,
    # percentage of repos with more external collabs than internal
    "percent_external_more": round(count_external_more / len(repos), 2) * 100,
    # percentage of repos with < 10 % external contributors
    "fewer_10_percent": round(count_fewer_10 / len(repos), 2) * 100,
}

# Scatterplot
# on X axis the percentage of external users
# on Y axis the total number of contributors
# the name of the project when hovering the data point

scatterplot = {}
for name, counts in repos.items():
    scatterplot[name] = {
        "percentage_external": round(counts["external"] / counts["total"], 2),
        "total": counts["total"],
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
    summary=summary,
    scatterplot=scatterplot,
)
with open("index.html", "w") as fd:
    fd.write(result)

with open("table-template.html", "r") as fd:
    template = Template(fd.read())

result = template.render(repos=repos)
with open("table.html", "w") as fd:
    fd.write(result)

# print to the terminal overlap in top 10
overlap = set(list(internal_sorted)[0:10]).intersection(
    set(list(external_sorted)[0:10])
)
print("Overlap top 10 external and internal collaborator projects: %s" % len(overlap))

# And let's save data for later too!
write_json(os.path.join(here, "data", "repos-contributors-counts.json"), repos)
write_json(os.path.join(here, "data", "filtered-sorted-totals.json"), filtered)
write_json(os.path.join(here, "data", "filtered-sorted-internal.json"), internal_sorted)
write_json(os.path.join(here, "data", "filtered-sorted-external.json"), external_sorted)
