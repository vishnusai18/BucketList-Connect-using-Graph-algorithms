"""
graph_builder.py

Thie file code helps Builds graph structures for the BucketList Connect project.

Graph model:
- User node: user:<user_id>
- Activity node: activity:<activity_name>
- Destination node: destination:<destination_name>

Edges:
- user to activity
- user to destination
"""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import Any

import pandas as pd


Adjacency = dict[str, set[str]]


def make_user_node(user_id: str) -> str:
    """
    Create a unique internal node ID for a user.
    """
    return f"user:{user_id}"


def make_activity_node(activity: str) -> str:
    """
    Create a unique internal node ID for an activity.
    """
    return f"activity:{activity.lower()}"


def make_destination_node(destination: str) -> str:
    """
    Create a unique internal node ID for a destination.
    """
    return f"destination:{destination.lower()}"


def add_undirected_edge(
    graph: defaultdict[str, set[str]],
    node_a: str,
    node_b: str,
) -> None:
    """
    Add an undirected edge to the adjacency-list graph.
    """
    graph[node_a].add(node_b)
    graph[node_b].add(node_a)


def build_preference_graph(
    df: pd.DataFrame,
) -> tuple[Adjacency, dict[str, str], dict[str, str]]:
    """
    Build a graph connecting users to activities and destinations.

    Returns:
    - graph: adjacency list
    - node_types: node ID to node type
    - node_labels: node ID to readable label
    """
    graph: defaultdict[str, set[str]] = defaultdict(set)
    node_types: dict[str, str] = {}
    node_labels: dict[str, str] = {}

    for _, row in df.iterrows():
        user_node = make_user_node(str(row["user_id"]))

        node_types[user_node] = "user"
        node_labels[user_node] = str(row["name"])

        graph[user_node]

        for activity in row["activities"]:
            activity_node = make_activity_node(activity)

            node_types[activity_node] = "activity"
            node_labels[activity_node] = activity

            add_undirected_edge(graph, user_node, activity_node)

        for destination in row["destinations"]:
            destination_node = make_destination_node(destination)

            node_types[destination_node] = "destination"
            node_labels[destination_node] = destination

            add_undirected_edge(graph, user_node, destination_node)

    return dict(graph), node_types, node_labels


def build_user_interest_map(df: pd.DataFrame) -> dict[str, set[str]]:
    """
    Build a mapping from each user to their activity and destination nodes.
    """
    user_interest_map: dict[str, set[str]] = {}

    for _, row in df.iterrows():
        user_node = make_user_node(str(row["user_id"]))

        interests = set()

        for activity in row["activities"]:
            interests.add(make_activity_node(activity))

        for destination in row["destinations"]:
            interests.add(make_destination_node(destination))

        user_interest_map[user_node] = interests

    return user_interest_map


def build_user_lookup(df: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """
    Create a lookup table for user details.
    """
    lookup: dict[str, dict[str, Any]] = {}

    for _, row in df.iterrows():
        user_node = make_user_node(str(row["user_id"]))

        lookup[user_node] = {
            "user_id": str(row["user_id"]),
            "name": str(row["name"]),
            "email": str(row["email"]),
            "activities": row["activities"],
            "destinations": row["destinations"],
        }

    return lookup


def derive_user_similarity_graph(
    user_interest_map: dict[str, set[str]],
    min_shared_items: int = 1,
) -> tuple[Adjacency, dict[tuple[str, str], dict[str, Any]]]:
    """
    Build a user-to-user similarity graph.

    Two users are connected if they share at least min_shared_items
    activities or destinations.
    """
    interest_to_users: defaultdict[str, set[str]] = defaultdict(set)

    for user_node, interests in user_interest_map.items():
        for interest in interests:
            interest_to_users[interest].add(user_node)

    pair_to_shared: defaultdict[tuple[str, str], set[str]] = defaultdict(set)

    for interest, users in interest_to_users.items():
        sorted_users = sorted(users)

        for user_a, user_b in combinations(sorted_users, 2):
            pair_to_shared[(user_a, user_b)].add(interest)

    similarity_graph: defaultdict[str, set[str]] = defaultdict(set)
    edge_details: dict[tuple[str, str], dict[str, Any]] = {}

    for user_node in user_interest_map:
        similarity_graph[user_node]

    for (user_a, user_b), shared_items in pair_to_shared.items():
        if len(shared_items) >= min_shared_items:
            similarity_graph[user_a].add(user_b)
            similarity_graph[user_b].add(user_a)

            union_size = len(user_interest_map[user_a] | user_interest_map[user_b])

            if union_size:
                jaccard = len(shared_items) / union_size
            else:
                jaccard = 0.0

            edge_details[(user_a, user_b)] = {
                "shared_count": len(shared_items),
                "shared_items": shared_items,
                "jaccard": jaccard,
            }

    return dict(similarity_graph), edge_details