import numpy as np
from sklearn.neighbors import kneighbors_graph
import networkx as nx
import matplotlib.pyplot as plt
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore')

def find_optimal_neighbors_fast(points, target_zones_range=(5, 20), max_neighbors=10):
    """
    Fast heuristic to find optimal number of neighbors based on target zone count.
    Uses binary search for efficiency.
    """
    n_points = len(points)
    low, high = 2, min(max_neighbors, n_points - 1)
    best_k = 3
    best_zone_count = 0
    
    # Quick heuristic: start with sqrt(n) as initial guess
    initial_k = max(2, int(np.sqrt(n_points)))
    
    # Test initial k
    A = kneighbors_graph(points, n_neighbors=initial_k, mode='connectivity', include_self=False)
    G = nx.from_scipy_sparse_array(A)
    zones = list(nx.connected_components(G))
    zone_count = len(zones)
    
    if target_zones_range[0] <= zone_count <= target_zones_range[1]:
        return initial_k, zone_count
    
    # Binary search for optimal k
    for _ in range(5):  # Limit iterations for efficiency
        mid = (low + high) // 2
        A = kneighbors_graph(points, n_neighbors=mid, mode='connectivity', include_self=False)
        G = nx.from_scipy_sparse_array(A)
        zones = list(nx.connected_components(G))
        zone_count = len(zones)
        
        if target_zones_range[0] <= zone_count <= target_zones_range[1]:
            return mid, zone_count
        elif zone_count < target_zones_range[0]:
            high = mid - 1  # Too few zones, decrease k
        else:
            low = mid + 1   # Too many zones, increase k
            
        # Track best so far
        if abs(zone_count - np.mean(target_zones_range)) < abs(best_zone_count - np.mean(target_zones_range)):
            best_k = mid
            best_zone_count = zone_count
    
    return best_k, best_zone_count

def generate_vibrant_colors(num_colors):
    """
    Generate vibrant, distinct colors for zones.
    Uses HSV color space for better color distribution.
    """
    colors = []
    for i in range(num_colors):
        hue = i / num_colors
        saturation = 0.8 + 0.2 * (i % 3) / 3  # Vary saturation
        value = 0.7 + 0.3 * (i % 2) / 2      # Vary brightness
        
        # Convert HSV to RGB
        h_i = int(hue * 6)
        f = hue * 6 - h_i
        p = value * (1 - saturation)
        q = value * (1 - f * saturation)
        t = value * (1 - (1 - f) * saturation)
        
        if h_i == 0:
            r, g, b = value, t, p
        elif h_i == 1:
            r, g, b = q, value, p
        elif h_i == 2:
            r, g, b = p, value, t
        elif h_i == 3:
            r, g, b = p, q, value
        elif h_i == 4:
            r, g, b = t, p, value
        else:
            r, g, b = value, p, q
            
        colors.append((r, g, b))
    
    return colors

def calculate_optimal_zone_range(n_points, density_factor=0.1):
    """
    Dynamically calculate optimal zone range based on point count and density.
    """
    # Base calculation on point count with logarithmic scaling
    base_zones = max(3, int(np.log(n_points) * 2))
    min_zones = max(2, int(base_zones * 0.6))
    max_zones = min(n_points // 5, int(base_zones * 1.4))  # Avoid too many zones
    
    return (min_zones, max_zones)

def main():
    # Generate random point cloud
    np.random.seed(42)  # For reproducible results
    n_points = 200
    points = np.random.rand(n_points, 2)
    
    print(f"Generated {n_points} random points")
    print("=" * 50)
    
    # Dynamically calculate optimal zone range based on data characteristics
    target_zones_range = calculate_optimal_zone_range(n_points)
    print(f"Dynamically calculated target zone range: {target_zones_range}")
    
    # Find optimal number of neighbors with dynamic zone range
    optimal_k, zone_count = find_optimal_neighbors_fast(points, target_zones_range)
    print(f"Optimal number of neighbors: {optimal_k}")
    print(f"Actual zones found: {zone_count}")
    
    # Build k-NN graph with optimal neighbors
    A = kneighbors_graph(points, n_neighbors=optimal_k, mode='connectivity', include_self=False)
    
    # Convert to networkx graph
    G = nx.from_scipy_sparse_array(A)
    
    # Find connected components (zones)
    zones = list(nx.connected_components(G))
    print(f"Found {len(zones)} connected components (zones)")
    
    # Generate vibrant colors for zones
    zone_colors = generate_vibrant_colors(len(zones))
    
    # Assign zone colors to points
    colors = []
    zone_map = {}
    for i, comp in enumerate(zones):
        color = zone_colors[i]
        for idx in comp:
            zone_map[idx] = color
    
    # Create color list for all points
    for i in range(len(points)):
        colors.append(zone_map.get(i, (0.5, 0.5, 0.5)))  # Gray for unassigned (shouldn't happen)
    
    # Plot the graph
    plt.figure(figsize=(12, 8))
    
    # Create position dictionary
    pos = {i: points[i] for i in range(len(points))}
    
    # Draw the graph
    nx.draw(G, pos=pos, 
            node_color=colors, 
            with_labels=False, 
            node_size=100, 
            edge_color='gray', 
            alpha=0.7,
            width=0.5)
    
    # Add title and information
    plt.title(f'k-NN Graph with Dynamic Neighbor Selection (k={optimal_k})\n{len(zones)} zones identified', 
              fontsize=14, fontweight='bold')
    plt.xlabel('X coordinate')
    plt.ylabel('Y coordinate')
    
    # Add legend for zones
    from matplotlib.patches import Patch
    legend_elements = []
    for i, color in enumerate(zone_colors[:min(10, len(zone_colors))]):  # Show first 10 zones in legend
        legend_elements.append(Patch(facecolor=color, label=f'Zone {i+1}'))
    
    if len(zone_colors) > 10:
        legend_elements.append(Patch(facecolor='lightgray', label=f'... and {len(zone_colors)-10} more zones'))
    
    plt.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))
    
    plt.tight_layout()
    plt.show()
    
    # Print comprehensive statistics
    print("\n" + "=" * 50)
    print("COMPREHENSIVE ZONE ANALYSIS")
    print("=" * 50)
    
    # Zone statistics
    zone_sizes = [len(zone) for zone in zones]
    largest_zone = max(zone_sizes)
    smallest_zone = min(zone_sizes)
    avg_zone_size = np.mean(zone_sizes)
    
    print(f"Total points: {n_points}")
    print(f"Number of zones: {len(zones)}")
    print(f"Largest zone: {largest_zone} points")
    print(f"Smallest zone: {smallest_zone} points")
    print(f"Average zone size: {avg_zone_size:.1f} points")
    print(f"Connectivity ratio: {len(zones) / n_points:.3f}")
    
    print("\nZone Statistics:")
    for i, zone in enumerate(zones):
        print(f"Zone {i+1}: {len(zone)} points")
    
    print("\n" + "=" * 50)
    print("Analysis complete!")

if __name__ == "__main__":
    main()
