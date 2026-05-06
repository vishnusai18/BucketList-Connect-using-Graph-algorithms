"""
main.py

"""

from __future__ import annotations

import argparse

from src.algorithms import bfs, connected_components, dfs
from src.data_loader import load_visitors_dataset
from src.graph_builder import (
    build_preference_graph,
    build_user_interest_map,
    build_user_lookup,
    derive_user_similarity_graph,
    make_user_node,
)
from src.similarity import recommend_interests, top_similar_users


def format_node(
    node: str,
    node_labels: dict[str, str],
) -> str:
    """
    Return a readable graph node.
    """
    label = node_labels.get(node, node)
    node_type = node.split(":", 1)[0]

    return f"{label} ({node_type})"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="BucketList Connect graph project"
    )

    parser.add_argument(
        "--data",
        default="data",
        help="Path to dataset file or data folder",
    )

    parser.add_argument(
        "--max-users",
        type=int,
        default=500,
        help="Maximum number of users to load",
    )

    parser.add_argument(
        "--user-id",
        default=None,
        help="User ID to analyze. If not provided, the first user is selected.",
    )

    args = parser.parse_args()

    df = load_visitors_dataset(
        dataset_path=args.data,
        max_users=args.max_users,
    )

    preference_graph, node_types, node_labels = build_preference_graph(df)
    user_interest_map = build_user_interest_map(df)
    user_lookup = build_user_lookup(df)

    similarity_graph, edge_details = derive_user_similarity_graph(
        user_interest_map=user_interest_map,
        min_shared_items=1,
    )

    selected_user_id = args.user_id or str(df.iloc[0]["user_id"])
    selected_user = make_user_node(selected_user_id)

    if selected_user not in user_lookup:
        print(f"User ID {selected_user_id} was not found.")
        print("Available user IDs:")
        print(", ".join(df["user_id"].astype(str).head(20)))
        return


    print("BucketList Connect")


    print(f"\nUsers loaded: {len(df)}")
    print(f"Preference graph nodes: {len(preference_graph)}")
    print(f"Preference graph edges: {sum(len(v) for v in preference_graph.values()) // 2}")
    print(f"Similarity graph users: {len(similarity_graph)}")
    print(f"Similarity graph edges: {sum(len(v) for v in similarity_graph.values()) // 2}")

    selected_details = user_lookup[selected_user]

    print("\nSelected User")
  
    print(f"Name: {selected_details['name']}")
    print(f"Email: {selected_details['email']}")
    print(f"Activities: {', '.join(selected_details['activities'])}")
    print(f"Destinations: {', '.join(selected_details['destinations'])}")

    print("\nBFS from Selected User")
 

    bfs_order, distances, _ = bfs(
        graph=preference_graph,
        start_node=selected_user,
    )

    for node in bfs_order[:25]:
        print(f"Distance {distances[node]}: {format_node(node, node_labels)}")

    print("\nDFS from Selected User")
 

    dfs_order = dfs(
        graph=preference_graph,
        start_node=selected_user,
    )

    for node in dfs_order[:25]:
        print(format_node(node, node_labels))

    print("\nConnected Components in User Similarity Graph")
 

    components = connected_components(similarity_graph)

    for index, component in enumerate(components[:10], start=1):
        names = [
            user_lookup[user]["name"]
            for user in component
            if user in user_lookup
        ]

        print(f"Community {index}: {len(component)} users")
        print("  " + ", ".join(names[:15]))

    print("\nTop Similar Users")
   

    similar_users = top_similar_users(
        selected_user=selected_user,
        user_interest_map=user_interest_map,
        user_lookup=user_lookup,
        node_labels=node_labels,
        top_k=5,
    )

    if not similar_users:
        print("No similar users found.")
    else:
        for rank, user in enumerate(similar_users, start=1):
            print(
                f"{rank}. {user['name']} | "
                f"shared={user['shared_count']} | "
                f"jaccard={user['jaccard_similarity']}"
            )

            print("   Shared items:", ", ".join(user["shared_items"]))

    print("\nRecommended Activities/Destinations")


    recommendations = recommend_interests(
        selected_user=selected_user,
        similar_users=similar_users,
        user_interest_map=user_interest_map,
        node_labels=node_labels,
        limit=10,
    )

    if not recommendations:
        print("No recommendations found.")
    else:
        for recommendation in recommendations:
            print(
                f"- {recommendation['recommendation']} "
                f"({recommendation['type']}) | "
                f"score={recommendation['score']}"
            )


if __name__ == "__main__":
    main()