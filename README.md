# BucketList-Connect-using-Graph-algorithms
This repo contains the code files for my msml606 project 2 

# BucketList Connect

BucketList Connect is a graph-based application that discovers similar people using shared activities and bucket-list destinations.

## Main Idea

The project represents the visitor preference dataset as a graph:

- User nodes
- Activity nodes
- Destination nodes
- Edges between users and their preferred activities/destinations

A user-to-user similarity graph is also created where two users are connected if they share at least one activity or destination.

## Algorithms Used

The project manually implements:

- Breadth-First Search, also called BFS
- Depth-First Search, also called DFS
- Connected Components
- Similarity Matching using shared interests and Jaccard similarity

These graph algorithms are central to the application.
