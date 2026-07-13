import networkx as nx
import logging

logger = logging.getLogger(__name__)

class ClinicalKnowledgeGraph:
    def __init__(self):
        self.graph = nx.Graph()

    def add_data(self, entities: list, relationships: list):
        """
        Ingests entities and relationships into the graph.
        """
        for entity in entities:
            if not self.graph.has_node(entity):
                self.graph.add_node(entity)

        for rel in relationships:
            source = rel.source
            target = rel.target
            relation = rel.relation
            
            if not self.graph.has_node(source):
                self.graph.add_node(source)
            if not self.graph.has_node(target):
                self.graph.add_node(target)
                
            if self.graph.has_edge(source, target):
                self.graph[source][target]['weight'] += 1
            else:
                self.graph.add_edge(source, target, weight=1, relation=relation)
                
    def get_relevant_context(self, seed_entities: list, max_depth: int = 2, top_k: int = 10) -> str:
        """
        Performs a weighted BFS traversal starting from seed_entities to extract a contextual subgraph.
        """
        if not seed_entities:
            return ""

        visited = set()
        queue = [(e, 0) for e in seed_entities if self.graph.has_node(e)]
        relevant_edges = []
        
        while queue:
            # Sort queue by weight heuristically, or just simple BFS. 
            # Simple BFS with neighbor sorting is used here.
            current_node, depth = queue.pop(0)
            if current_node in visited or depth >= max_depth:
                continue
                
            visited.add(current_node)
            
            # Get neighbors and sort by edge weight
            neighbors = list(self.graph.neighbors(current_node))
            neighbors.sort(key=lambda n: self.graph[current_node][n].get('weight', 1), reverse=True)
            
            for neighbor in neighbors:
                if neighbor not in visited:
                    edge_data = self.graph[current_node][neighbor]
                    relevant_edges.append({
                        "source": current_node,
                        "target": neighbor,
                        "relation": edge_data.get("relation", "related to"),
                        "weight": edge_data.get("weight", 1)
                    })
                    queue.append((neighbor, depth + 1))
                    
        # Sort collected edges by weight and take top_k
        relevant_edges.sort(key=lambda x: x['weight'], reverse=True)
        top_edges = relevant_edges[:top_k]
        
        if not top_edges:
            return ""
            
        context_lines = []
        for edge in top_edges:
            context_lines.append(f"{edge['source']} is {edge['relation']} {edge['target']} (strength: {edge['weight']})")
            
        return "Graph Relationships:\n" + "\n".join(context_lines)

# Singleton instance for the session
global_graph = ClinicalKnowledgeGraph()

def get_graph():
    return global_graph
