"""知识图谱数据构建器"""

from __future__ import annotations

from ..models.schemas import GraphData, GraphEdge, GraphNode
from .wiki_manager import WikiManager


class GraphBuilder:
    """从 Wiki 页面的 [[wikilinks]] 构建图谱数据"""

    def __init__(self, wiki: WikiManager | None = None) -> None:
        self.wiki = wiki or WikiManager()

    def build(self) -> GraphData:
        """构建完整的图谱数据"""
        pages = self.wiki.list_pages()
        all_links = self.wiki.get_all_links()

        # 构建节点
        node_map: dict[str, GraphNode] = {}
        for p in pages:
            node_map[p.slug] = GraphNode(
                id=p.slug,
                label=p.title,
                category=p.category,
                size=0,
            )

        # 构建边并计算节点大小
        edges: list[GraphEdge] = []
        seen_edges: set[tuple[str, str]] = set()

        for source_slug, targets in all_links.items():
            for target_slug in targets:
                # 即使目标页面不存在也添加边（可能是缺失页面）
                if target_slug not in node_map:
                    node_map[target_slug] = GraphNode(
                        id=target_slug,
                        label=target_slug,
                        category="missing",
                        size=0,
                    )

                edge_key = (source_slug, target_slug)
                if edge_key not in seen_edges:
                    seen_edges.add(edge_key)
                    edges.append(GraphEdge(source=source_slug, target=target_slug))

                    # 双向增加连接数
                    node_map[source_slug].size += 1
                    node_map[target_slug].size += 1

        # size 至少为 1
        for node in node_map.values():
            node.size = max(node.size, 1)

        return GraphData(
            nodes=list(node_map.values()),
            edges=edges,
        )

    def get_neighbors(self, slug: str, depth: int = 1) -> GraphData:
        """获取指定节点的邻居子图"""
        full_graph = self.build()

        # BFS 获取指定深度的邻居
        visited: set[str] = {slug}
        frontier: set[str] = {slug}

        for _ in range(depth):
            next_frontier: set[str] = set()
            for edge in full_graph.edges:
                if edge.source in frontier:
                    next_frontier.add(edge.target)
                if edge.target in frontier:
                    next_frontier.add(edge.source)
            frontier = next_frontier - visited
            visited |= frontier

        # 过滤节点和边
        nodes = [n for n in full_graph.nodes if n.id in visited]
        edges = [
            e for e in full_graph.edges
            if e.source in visited and e.target in visited
        ]

        return GraphData(nodes=nodes, edges=edges)
