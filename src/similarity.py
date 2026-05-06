"""
similarity.py

This files code contains simi;arity logic to fsind similary connection susing jaccard similarity
"""

from __future__ import annotations

from typing import Any


def readable_interest_name(
    node: str,
    node_labels: dict[str, str],
) -> str:
    """
    Convert internal graph node ID into readable name.
    """
    return node_labels.get(node, node.split(":", 1)[-1].title())


def top_similar_users(
    selected_user: str,
    user_interest_map: dict[str, set[str]],
    user_lookup: dict[str, dict[str, Any]],
    node_labels: dict[str, str],
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """
    Find most similar users to the selected user.

    Similarity uses:
    - number of shared activities/destinations
    - Jaccard similarity
    """
    if selected_user not in user_interest_map:
        return []

    selected_interests = user_interest_map[selected_user]
    results = []

    for other_user, other_interests in user_interest_map.items():
        if other_user == selected_user:
            continue

        shared = selected_interests & other_interests
        union = selected_interests | other_interests

        if not shared:
            continue

        if union:
            jaccard = len(shared) / len(union)
        else:
            jaccard = 0.0

        results.append(
            {
                "user_node": other_user,
                "user_id": user_lookup[other_user]["user_id"],
                "name": user_lookup[other_user]["name"],
                "email": user_lookup[other_user]["email"],
                "shared_count": len(shared),
                "jaccard_similarity": round(jaccard, 3),
                "shared_items": [
                    readable_interest_name(item, node_labels)
                    for item in sorted(shared)
                ],
            }
        )

    results.sort(
        key=lambda item: (item["shared_count"], item["jaccard_similarity"]),
        reverse=True,
    )

    return results[:top_k]


def recommend_interests(
    selected_user: str,
    similar_users: list[dict[str, Any]],
    user_interest_map: dict[str, set[str]],
    node_labels: dict[str, str],
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Recommend activities or destinations.

    If similar users have interests that the selected user does not have,
    those interests are recommended.
    """
    if selected_user not in user_interest_map:
        return []

    selected_interests = user_interest_map[selected_user]
    recommendation_scores: dict[str, int] = {}

    for user in similar_users:
        other_user = user["user_node"]

        for interest in user_interest_map[other_user]:
            if interest not in selected_interests:
                recommendation_scores[interest] = recommendation_scores.get(interest, 0) + 1

    recommendations = []

    for interest, score in recommendation_scores.items():
        interest_type = interest.split(":", 1)[0]

        recommendations.append(
            {
                "recommendation": readable_interest_name(interest, node_labels),
                "type": interest_type,
                "score": score,
            }
        )

    recommendations.sort(key=lambda item: item["score"], reverse=True)

    return recommendations[:limit]