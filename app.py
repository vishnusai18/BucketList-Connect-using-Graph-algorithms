"""
app.py

Streamlit frontend for BucketList Connect.

Run:
streamlit run app.py
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import streamlit as st

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


st.set_page_config(
    page_title="BucketList Connect",
    layout="wide",
)


@st.cache_data
def load_data(
    dataset_path: str,
    max_users: int,
) -> pd.DataFrame:
    """
    Load dataset for Streamlit.
    """
    return load_visitors_dataset(
        dataset_path=dataset_path,
        max_users=max_users,
    )


def build_networkx_neighborhood(
    graph: dict[str, set[str]],
    start_node: str,
    node_labels: dict[str, str],
    max_nodes: int = 35,
) -> nx.Graph:
    """
    Build a small graph for visualization.

    NetworkX is only used for drawing.
    BFS, DFS, and connected components are manually implemented separately.
    """
    bfs_order, _, _ = bfs(
        graph=graph,
        start_node=start_node,
    )

    selected_nodes = set(bfs_order[:max_nodes])

    visual_graph = nx.Graph()

    for node in selected_nodes:
        visual_graph.add_node(
            node,
            label=node_labels.get(node, node),
        )

    for node in selected_nodes:
        for neighbor in graph.get(node, set()):
            if neighbor in selected_nodes:
                visual_graph.add_edge(node, neighbor)

    return visual_graph


def draw_graph(
    graph: nx.Graph,
    node_labels: dict[str, str],
) -> None:
    """
    Draw graph using matplotlib.
    """
    fig, ax = plt.subplots(figsize=(11, 7))

    position = nx.spring_layout(
        graph,
        seed=42,
    )

    labels = {
        node: node_labels.get(node, node)
        for node in graph.nodes()
    }

    nx.draw_networkx_nodes(
        graph,
        position,
        node_size=700,
        ax=ax,
    )

    nx.draw_networkx_edges(
        graph,
        position,
        alpha=0.5,
        ax=ax,
    )

    nx.draw_networkx_labels(
        graph,
        position,
        labels=labels,
        font_size=8,
        ax=ax,
    )

    ax.set_axis_off()

    st.pyplot(fig)


def main() -> None:
    st.title("BucketList Connect")

    st.write(
        "A graph-based application to discover similar users using shared "
        "activities and bucket-list destinations."
    )

    with st.sidebar:
        st.header("Dataset Settings")

        dataset_path = st.text_input(
            "Dataset path",
            value="data",
            help="Use 'data' to automatically load the CSV/XLSX file inside the data folder.",
        )

        max_users = st.slider(
            "Maximum users to load",
            min_value=10,
            max_value=10000,
            value=500,
            step=10,
        )

        top_k = st.slider(
            "Number of similar users",
            min_value=1,
            max_value=20,
            value=5,
        )

    df = load_data(
        dataset_path=dataset_path,
        max_users=max_users,
    )

    preference_graph, node_types, node_labels = build_preference_graph(df)
    user_interest_map = build_user_interest_map(df)
    user_lookup = build_user_lookup(df)

    similarity_graph, edge_details = derive_user_similarity_graph(
        user_interest_map=user_interest_map,
        min_shared_items=1,
    )

    user_options = {
        f"{row['name']} | ID: {row['user_id']}": str(row["user_id"])
        for _, row in df.iterrows()
    }

    selected_label = st.selectbox(
        "Select a user",
        list(user_options.keys()),
    )

    selected_user_id = user_options[selected_label]
    selected_user = make_user_node(selected_user_id)

    user_details = user_lookup[selected_user]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Users Loaded", len(df))

    col2.metric(
        "Preference Graph Nodes",
        len(preference_graph),
    )

    col3.metric(
        "Preference Graph Edges",
        sum(len(v) for v in preference_graph.values()) // 2,
    )

    col4.metric(
        "Similarity Graph Edges",
        sum(len(v) for v in similarity_graph.values()) // 2,
    )

    st.subheader("Selected User Profile")

    st.write(f"**Name:** {user_details['name']}")
    st.write(f"**Email:** {user_details['email']}")
    st.write(f"**Activities:** {', '.join(user_details['activities'])}")
    st.write(f"**Bucket-list destinations:** {', '.join(user_details['destinations'])}")

    st.subheader("Top Similar Users")

    similar_users = top_similar_users(
        selected_user=selected_user,
        user_interest_map=user_interest_map,
        user_lookup=user_lookup,
        node_labels=node_labels,
        top_k=top_k,
    )

    if similar_users:
        similar_df = pd.DataFrame(
            [
                {
                    "Name": user["name"],
                    "Email": user["email"],
                    "Shared Count": user["shared_count"],
                    "Jaccard Similarity": user["jaccard_similarity"],
                    "Shared Items": ", ".join(user["shared_items"]),
                }
                for user in similar_users
            ]
        )

        st.dataframe(
            similar_df,
            use_container_width=True,
        )
    else:
        st.info("No similar users found for this selected user.")

    st.subheader("Recommendations")

    recommendations = recommend_interests(
        selected_user=selected_user,
        similar_users=similar_users,
        user_interest_map=user_interest_map,
        node_labels=node_labels,
        limit=10,
    )

    if recommendations:
        st.dataframe(
            pd.DataFrame(recommendations),
            use_container_width=True,
        )
    else:
        st.info("No recommendations found.")

    st.subheader("BFS and DFS Exploration")

    bfs_order, distances, _ = bfs(
        graph=preference_graph,
        start_node=selected_user,
    )

    dfs_order = dfs(
        graph=preference_graph,
        start_node=selected_user,
    )

    col_left, col_right = st.columns(2)

    with col_left:
        st.write("**BFS Visit Order**")

        bfs_rows = []

        for node in bfs_order[:25]:
            bfs_rows.append(
                {
                    "Node": node_labels.get(node, node),
                    "Type": node.split(":", 1)[0],
                    "Distance": distances[node],
                }
            )

        st.dataframe(
            pd.DataFrame(bfs_rows),
            use_container_width=True,
        )

    with col_right:
        st.write("**DFS Visit Order**")

        dfs_rows = []

        for index, node in enumerate(dfs_order[:25], start=1):
            dfs_rows.append(
                {
                    "Visit Order": index,
                    "Node": node_labels.get(node, node),
                    "Type": node.split(":", 1)[0],
                }
            )

        st.dataframe(
            pd.DataFrame(dfs_rows),
            use_container_width=True,
        )

    st.subheader("User Communities Using Connected Components")

    communities = connected_components(similarity_graph)

    community_rows = []

    for index, component in enumerate(communities, start=1):
        names = [
            user_lookup[user]["name"]
            for user in component
            if user in user_lookup
        ]

        community_rows.append(
            {
                "Community": index,
                "Number of Users": len(component),
                "Users": ", ".join(names[:20]),
            }
        )

    st.dataframe(
        pd.DataFrame(community_rows),
        use_container_width=True,
    )

    st.subheader("Graph Visualization")

    st.caption(
        "This graph shows a small BFS neighborhood around the selected user. "
        "NetworkX is only used for visualization."
    )

    visual_graph = build_networkx_neighborhood(
        graph=preference_graph,
        start_node=selected_user,
        node_labels=node_labels,
        max_nodes=35,
    )

    draw_graph(
        graph=visual_graph,
        node_labels=node_labels,
    )


if __name__ == "__main__":
    main()