import os
os.chdir(r"C:\Users\Documents\Python")#Chemin a modifier
import pandas as pd
import numpy as np
import re
from Anybody_Package.Anybody_LoadOutput.Tools import load_results_from_file
from Anybody_Package.Anybody_Graph.GraphFunctions import graph
from Anybody_Package.Anybody_Graph.GraphFunctions import COP_graph
from Anybody_Package.Anybody_Graph.GraphFunctions import muscle_graph
from Anybody_Package.Anybody_Graph.GraphFunctions import define_simulations_line_style
from Anybody_Package.Anybody_Graph.GraphFunctions import define_simulation_description
from Anybody_Package.Anybody_Graph.GraphFunctions import define_COP_contour
from Anybody_Package.Anybody_LoadOutput.LoadOutput import combine_simulation_cases
from Anybody_Package.Anybody_LoadOutput.LoadLiterature import load_literature_data
from Anybody_Package.Anybody_Graph.GraphFunctions import ForceMeasure_bar_plot_direction
from Anybody_Package.Anybody_Graph import PremadeGraphs
import matplotlib
import matplotlib.pyplot as plt

# Variable to store the path to a file with selected results
SELECTED_RESULTS_FILE = None

def check_annotation_collision(new_pos, existing_positions, min_distance=90):
    """
    Vérifie si une nouvelle position d'annotation entre en collision avec les existantes
    
    Args:
        new_pos: tuple (x, y) de la nouvelle position (en coordonnées d'écran)
        existing_positions: liste des positions existantes [(x1, y1), (x2, y2), ...]
        min_distance: distance minimale entre les annotations (augmentée à 100)
    
    Returns:
        bool: True s'il y a collision, False sinon
    """
    for existing_pos in existing_positions:
        distance = np.sqrt((new_pos[0] - existing_pos[0])**2 + (new_pos[1] - existing_pos[1])**2)
        if distance < min_distance:
            return True
    return False

def find_best_annotation_position(point_x, point_y, existing_positions, ax, type_priority=0, min_distance=90):
    """
    Trouve la meilleure position pour une annotation sans collision
    
    Args:
        point_x, point_y: coordonnées du point à annoter (en coordonnées de données)
        existing_positions: liste des positions d'annotations existantes (en coordonnées d'écran)
        ax: axes matplotlib pour la conversion de coordonnées
        type_priority: priorité du type (0 = référence, plus élevé = moins prioritaire)
        min_distance: distance minimale entre annotations
    
    Returns:
        tuple: (offset_x, offset_y) pour l'annotation
    """
    # Convertir le point en coordonnées d'écran
    point_screen = ax.transData.transform((point_x, point_y))
    
    # Distance de base plus proche et moins dépendante de la priorité
    base_distance = 30 + (type_priority * 8)  # Distances plus courtes
    
    # Créer des positions candidates avec des distances graduelles plus fines
    candidate_offsets = []
    
    # Première série: positions très proches (priorité maximale)
    close_angles = [0, np.pi/4, np.pi/2, 3*np.pi/4, np.pi, 5*np.pi/4, 3*np.pi/2, 7*np.pi/4]
    for angle in close_angles:
        for radius in [base_distance, base_distance*1.15, base_distance*1.3]:
            offset_x = radius * np.cos(angle)
            offset_y = radius * np.sin(angle)
            candidate_offsets.append((offset_x, offset_y))
    
    # Deuxième série: positions moyennes avec plus de granularité
    medium_angles = np.linspace(0, 2*np.pi, 16, endpoint=False)
    for angle in medium_angles:
        for radius in [base_distance*1.45, base_distance*1.6, base_distance*1.8, base_distance*2.0]:
            offset_x = radius * np.cos(angle)
            offset_y = radius * np.sin(angle)
            candidate_offsets.append((offset_x, offset_y))
    
    # Troisième série: positions plus éloignées (si vraiment nécessaire)
    far_angles = np.linspace(0, 2*np.pi, 12, endpoint=False)
    for angle in far_angles:
        for radius in [base_distance*2.3, base_distance*2.7, base_distance*3.2]:
            offset_x = radius * np.cos(angle)
            offset_y = radius * np.sin(angle)
            candidate_offsets.append((offset_x, offset_y))
    
    # Trier les positions par distance croissante (préférer les positions proches)
    candidate_offsets.sort(key=lambda pos: np.sqrt(pos[0]**2 + pos[1]**2))
    
    # Tester chaque position candidate avec distance adaptative
    for offset_x, offset_y in candidate_offsets:
        # Position de l'annotation en coordonnées d'écran
        annotation_screen_pos = (point_screen[0] + offset_x, point_screen[1] + offset_y)
        
        # Vérifier que l'annotation reste dans les limites du graphique
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        annotation_data_pos = ax.transData.inverted().transform(annotation_screen_pos)
        
        if (xlim[0] <= annotation_data_pos[0] <= xlim[1] and 
            ylim[0] <= annotation_data_pos[1] <= ylim[1]):
            
            # Distance adaptative: plus flexible pour les positions proches
            current_distance = np.sqrt(offset_x**2 + offset_y**2)
            adaptive_min_distance = min_distance if current_distance > base_distance*1.5 else min_distance*0.85
            
            # Vérifier les collisions avec toutes les annotations existantes
            if not check_annotation_collision(annotation_screen_pos, existing_positions, adaptive_min_distance):
                return offset_x, offset_y
    
    # Si aucune position n'est trouvée, utiliser une position de secours moins éloignée
    fallback_distance = base_distance * 2.5 + type_priority * 15
    fallback_angle = type_priority * 0.6  # Rotation basée sur la priorité
    return (fallback_distance * np.cos(fallback_angle), fallback_distance * np.sin(fallback_angle))

# Modified function for loading results
def _load_results_with_selection():
    import pickle
    import os
    
    # Directory for saved simulations
    SaveSimulationsDirectory = "C:/Users/Documents/Python/Saved Simulations"#chemin a modfier
    
    # If a selection file is specified, use it
    if SELECTED_RESULTS_FILE and os.path.exists(SELECTED_RESULTS_FILE):
        try:
            with open(SELECTED_RESULTS_FILE, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Error loading selection: {e}")
    
    # Otherwise, load results normally
    try:
        ResultsFile = os.path.join(SaveSimulationsDirectory, "Results.pkl")
        with open(ResultsFile, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Error loading results: {e}")
        return None

# Load results with selection handling
Results = _load_results_with_selection()


# Path to the directory for saving simulations
SaveSimulationsDirectory = "C:/Users/Documents/Python/Saved Simulations"#chemin a modfier

# Load results
Results = load_results_from_file(SaveSimulationsDirectory, "Results")

# Function to identify cases and use their real names
def identify_case_types():
    available_cases = list(Results.keys())
    
    if not available_cases:
        print("No cases available in the data")
        return {}
    
    print("\nAvailable cases in the data:")
    for i, case_name in enumerate(available_cases):
        print(f"{i+1}. {case_name}")
    
    type_cases = {}
    
    # Automatically identify the reference if it exists
    reference_pattern = r'ref|référence|reference|Référencev3|AnyBody Parameters'
    reference_case = None
    for case_name in available_cases:
        if re.search(reference_pattern, case_name, re.IGNORECASE):
            reference_case = case_name
            type_cases['Reference'] = case_name
            print(f"Reference case identified: {case_name}")
            break
    
    # Add all other cases with their original name
    for case_name in available_cases:
        if case_name != reference_case:  # Avoid duplicates with the reference
            # Use the case name directly as key
            type_cases[case_name] = case_name
            print(f"Case identified: {case_name}")
    
    return type_cases

from type_colors import FIXED_TYPE_COLORS #Avoir le fichier dans le meme dossier

def get_type_colors(type_cases):
    type_colors = {}
    used_colors = set()

    for type_key, case_name in type_cases.items():
        # Utiliser couleur fixe si disponible
        if case_name in FIXED_TYPE_COLORS:
            type_colors[type_key] = FIXED_TYPE_COLORS[case_name]
            used_colors.add(FIXED_TYPE_COLORS[case_name])
        elif type_key == 'Reference':
            type_colors[type_key] = FIXED_TYPE_COLORS['Reference']
        else:
            # Si non trouvé dans le dictionnaire, assigne une couleur par défaut
            type_colors[type_key] = '#cccccc'  # gris clair par défaut

    return type_colors


# Modified function to create improved AP and IS graphs with reference and type in same plot
def create_improved_ap_is_graphs(type_name, type_data, reference_data=None):
    """
    Creates improved graphs for AP and IS with subplots showing both reference and type
    
    Args:
        type_name: The type name (exact case name)
        type_data: The type data
        reference_data: The reference data
    """
    if type_data is None:
        print(f"No data for {type_name}")
        return
    
    # Extract type data
    angles = type_data['abduction']
    type_ap = type_data['AP']
    type_is = type_data['IS']
    
    # Extract reference data if available
    reference_ap = None
    reference_is = None
    reference_angles = None
    if reference_data is not None:
        reference_ap = reference_data['AP']
        reference_is = reference_data['IS']
        reference_angles = reference_data['abduction']
    
    # Calculate the overall min and max values for both datasets to determine scale
    all_values = []
    all_values.extend(type_ap)
    all_values.extend(type_is)
    if reference_ap is not None:
        all_values.extend(reference_ap)
    if reference_is is not None:
        all_values.extend(reference_is)
    
    # Calculate dynamic scale with some padding
    data_min = min(all_values)
    data_max = max(all_values)
    padding = (data_max - data_min) * 0.1  # 10% padding
    y_min = data_min - padding
    y_max = data_max + padding
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 16))
    
    # Configure AP (Anteroposterior) graph
    ax1.axhline(y=0, color='gray', linestyle='-', alpha=0.7, linewidth=1)
    min_angle = min(angles)
    max_angle = max(angles)
    ax1.fill_between([min_angle, max_angle], 0, y_max, color='lightblue', alpha=0.3, label='Anterior Zone')
    ax1.fill_between([min_angle, max_angle], y_min, 0, color='lightcoral', alpha=0.3, label='Posterior Zone')
    
    # Plot the reference curve first if available
    if reference_ap is not None and reference_angles is not None:
        ax1.plot(reference_angles, reference_ap, '--', label='Reference', linewidth=3, color='black', alpha=0.8)
    
    # Plot the type curve with the exact name
    type_label = type_name if type_name != 'Reference' else 'Reference'
    ax1.plot(angles, type_ap, 'o-', label=type_label, linewidth=2, markersize=8, color=type_colors[type_name])
    
    # Add explanatory annotations
    ax1.annotate('ANTERIOR', xy=(max_angle * 0.9, y_max * 0.4), 
                fontsize=12, ha='center', va='center', color='darkblue')
    ax1.annotate('POSTERIOR', xy=(max_angle * 0.9, y_min * 0.4), 
                fontsize=12, ha='center', va='center', color='darkred')
    
    # Configure AP graph appearance
    ax1.set_title(f'AP (Anteroposterior) Translations - {type_label}', fontsize=16, fontweight='bold')
    ax1.set_xlabel("Abduction Angle (°)", fontsize=14)
    ax1.set_ylabel('AP Translation (mm)', fontsize=14)
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.legend(fontsize=12, loc='upper left')
    
    # Define tick marks for angles
    step = max(1, len(angles) // 10)  # Limit the number of tick marks
    ax1.set_xticks(angles[::step])
    ax1.set_xticklabels([f"{int(angle)}°" for angle in angles[::step]])
    ax1.set_ylim(y_min, y_max)
    
    # Configure IS (Inferosuperior) graph - SAME SCALE
    ax2.axhline(y=0, color='gray', linestyle='-', alpha=0.7, linewidth=1)
    ax2.fill_between([min_angle, max_angle], 0, y_max, color='lightblue', alpha=0.3, label='Superior Zone')
    ax2.fill_between([min_angle, max_angle], y_min, 0, color='lightcoral', alpha=0.3, label='Inferior Zone')
    
    # Plot the reference curve first if available
    if reference_is is not None and reference_angles is not None:
        ax2.plot(reference_angles, reference_is, '--', label='Reference', linewidth=3, color='black', alpha=0.8)
    
    # Plot the type curve
    ax2.plot(angles, type_is, 'o-', label=type_label, linewidth=2, markersize=8, color=type_colors[type_name])
    
    # Add explanatory annotations for IS
    ax2.annotate('SUPERIOR', xy=(max_angle * 0.9, y_max * 0.4), 
                fontsize=12, ha='center', va='center', color='darkblue')
    ax2.annotate('INFERIOR', xy=(max_angle * 0.9, y_min * 0.4), 
                fontsize=12, ha='center', va='center', color='purple')
    
    # Configure IS graph appearance
    ax2.set_title(f'IS (Inferosuperior) Translations - {type_label}', fontsize=16, fontweight='bold')
    ax2.set_xlabel("Abduction angle (°)", fontsize=14)
    ax2.set_ylabel('IS Translation (mm)', fontsize=14)
    ax2.grid(True, linestyle='--', alpha=0.7)
    ax2.legend(fontsize=12, loc='upper left')
    
    # Define tick marks for angles
    ax2.set_xticks(angles[::step])
    ax2.set_xticklabels([f"{int(angle)}°" for angle in angles[::step]])
    ax2.set_ylim(y_min, y_max)
    
    # Adjust spacing
    plt.tight_layout(pad=4.0)
    plt.show()


# Function to create AP-IS trajectory plot for all types with dynamic axis scaling
def create_all_types_trajectory_plot(type_data, type_cases):
    """Version améliorée avec meilleure gestion des collisions"""
    fig, ax = plt.subplots(figsize=(14, 14))  # Figure plus grande pour plus d'espace

    # Collect all AP and IS values to determine the range
    all_ap_values = []
    all_is_values = []
    
    for type_name, data in type_data.items():
        if data is not None:
            all_ap_values.extend(data['AP'])
            all_is_values.extend(data['IS'])
    
    if not all_ap_values or not all_is_values:
        print("No data available for plotting")
        return
    
    # Calculate ranges with some padding
    ap_min, ap_max = min(all_ap_values), max(all_ap_values)
    is_min, is_max = min(all_is_values), max(all_is_values)
    
    # Add 12% padding to the ranges (équilibre entre espace et proximité)
    ap_padding = (ap_max - ap_min) * 0.12
    is_padding = (is_max - is_min) * 0.12
    
    ap_min -= ap_padding
    ap_max += ap_padding
    is_min -= is_padding
    is_max += is_padding
    
    # Make sure we include zero in both axes
    ap_min = min(ap_min, 0)
    ap_max = max(ap_max, 0)
    is_min = min(is_min, 0)
    is_max = max(is_max, 0)
    
    # Add lines to divide quadrants
    ax.axhline(y=0, color='gray', linestyle='-', alpha=0.7, linewidth=1)
    ax.axvline(x=0, color='gray', linestyle='-', alpha=0.7, linewidth=1)

    # Calculate the final axis limits for coloring (after equal scaling)
    ap_range = ap_max - ap_min
    is_range = is_max - is_min
    max_range = max(ap_range, is_range)
    
    ap_center = (ap_min + ap_max) / 2
    is_center = (is_min + is_max) / 2
    
    final_ap_min = ap_center - max_range/2
    final_ap_max = ap_center + max_range/2
    final_is_min = is_center - max_range/2
    final_is_max = is_center + max_range/2

    # Color the quadrants
    ax.fill_between([final_ap_min, 0], 0, final_is_max, color='lightblue', alpha=0.15)
    ax.fill_between([0, final_ap_max], 0, final_is_max, color='lightgreen', alpha=0.15)
    ax.fill_between([final_ap_min, 0], final_is_min, 0, color='lightcoral', alpha=0.15)
    ax.fill_between([0, final_ap_max], final_is_min, 0, color='lightyellow', alpha=0.15)

    # Add quadrant labels
    ax.annotate('POSTERIOR-SUPERIOR', xy=(final_ap_min/2, final_is_max*0.5), 
                fontsize=10, ha='center', va='center', color='darkblue')
    ax.annotate('ANTERIOR-SUPERIOR', xy=(final_ap_max/2, final_is_max*0.5), 
                fontsize=10, ha='center', va='center', color='darkgreen')
    ax.annotate('POSTERIOR-INFERIOR', xy=(final_ap_min/2, final_is_min*0.5), 
                fontsize=10, ha='center', va='center', color='darkred')
    ax.annotate('ANTERIOR-INFERIOR', xy=(final_ap_max/2, final_is_min*0.5), 
                fontsize=10, ha='center', va='center', color='darkorange')

    # Liste pour stocker les positions des annotations critiques
    critical_annotation_positions = []
    
    # Trier les types par priorité (référence en premier)
    type_priority = {}
    for i, type_name in enumerate(sorted(type_data.keys())):
        if type_name == 'Reference':
            type_priority[type_name] = 0  # Priorité maximale
        else:
            type_priority[type_name] = i + 1

    def plot_type(type_name, data, priority):
        nonlocal critical_annotation_positions
        
        if data is None:
            print(f"No data for {type_name}")
            return
    
        ap_data = data['AP']
        is_data = data['IS']
        angles = data['abduction']
        color = type_colors[type_name]
        label = type_name if type_name != 'Reference' else 'Reference'
    
        # Tracer la courbe
        ax.plot(ap_data, is_data, '-', color=color, linewidth=2, label=label)
        for i in range(1, len(angles) - 1):
            ax.plot(ap_data[i], is_data[i], 'o', color=color, markersize=6)
    
        ax.plot(ap_data[0], is_data[0], 'o', color='lime', markersize=12, 
                markeredgecolor=color, markeredgewidth=2)
        ax.plot(ap_data[-1], is_data[-1], 'o', color='red', markersize=12, 
                markeredgecolor=color, markeredgewidth=2)
    
        # Rechercher le max combiné (norme AP-IS) entre 30° et 60°
        indices_in_range = [i for i, a in enumerate(angles) if 10 <= a <= 120]
        if indices_in_range:
            max_idx = max(indices_in_range, key=lambda i: np.linalg.norm([ap_data[i], is_data[i]]))
            
            # Trouver la meilleure position pour l'annotation
            offset_x, offset_y = find_best_annotation_position(
                ap_data[max_idx], 
                is_data[max_idx], 
                critical_annotation_positions,
                ax,
                priority,
                min_distance=95  # Distance minimale réduite
            )
            
            # Convertir la position du point en coordonnées d'écran
            point_screen = ax.transData.transform((ap_data[max_idx], is_data[max_idx]))
            annotation_screen_pos = (point_screen[0] + offset_x, point_screen[1] + offset_y)
            
            # Ajouter cette position à la liste des positions occupées
            critical_annotation_positions.append(annotation_screen_pos)
    
            # Créer l'annotation avec une boîte plus distinctive
            annotation = ax.annotate(
                f"{angles[max_idx]:.0f}°\nAP={ap_data[max_idx]:.1f} mm\nIS={is_data[max_idx]:.1f} mm",
                xy=(ap_data[max_idx], is_data[max_idx]),
                xytext=(offset_x, offset_y),
                textcoords='offset points',
                fontsize=10,
                color=color,
                bbox=dict(boxstyle="round,pad=0.5", fc="white", ec=color, lw=2, alpha=0.95),
                arrowprops=dict(arrowstyle='->', color=color, lw=2, alpha=0.8),
                ha='center',
                va='center',
                zorder=15
            )

    # Plot all types selon leur priorité
    for type_name in sorted(type_priority.keys(), key=lambda x: type_priority[x]):
        if type_data[type_name] is not None:
            plot_type(type_name, type_data[type_name], type_priority[type_name])

    # Add origin marker
    ax.plot(0, 0, '+', color='black', markersize=15, markeredgewidth=3)
    origin_offset_x = (ap_max - ap_min) * 0.02
    origin_offset_y = (is_max - is_min) * 0.02
    ax.annotate('Origin (0,0)', xy=(0, 0), xytext=(origin_offset_x, -origin_offset_y), 
                color='black', fontsize=10, fontweight='bold')

    # Add legend markers
    ax.plot([], [], 'o', color='lime', markersize=12, markeredgecolor='black', 
            markeredgewidth=2, label='Start')
    ax.plot([], [], 'o', color='red', markersize=12, markeredgecolor='black', 
            markeredgewidth=2, label='End')
    
    # Configure plot
    ax.set_title('AP-IS Translation Trajectory', fontsize=18, fontweight='bold', pad=20)
    ax.set_xlabel('AP Translation (mm)\nNegative = Posterior, Positive = Anterior', fontsize=14)
    ax.set_ylabel('IS Translation (mm)\nNegative = Inferior, Positive = Superior', fontsize=14)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend(fontsize=12, loc='upper left')

    # Set equal ranges
    ax.set_xlim(final_ap_min, final_ap_max)
    ax.set_ylim(final_is_min, final_is_max)
    ax.set_aspect('equal')
    
    plt.tight_layout()
    plt.show()

# Function to create a comparison table for all types
def create_all_types_comparison_table(type_data, type_cases):
    # Define specific angles for the table
    specific_angles = [10,11, 15 ,20, 25, 30, 35, 40,45, 50,55, 60, 70, 80, 90, 100, 110, 120]
    
    # Find the common angle range
    min_angles = []
    max_angles = []
    for type_name, data in type_data.items():
        if data is not None:
            min_angles.append(min(data['abduction']))
            max_angles.append(max(data['abduction']))
    
    if not min_angles or not max_angles:
        print("No data available to create the table")
        return None
    
    common_min = max(min_angles)
    common_max = min(max_angles)
    
    # Adjust specific angles to the available range
    valid_angles = [a for a in specific_angles if a >= common_min and a <= common_max]
    if not valid_angles:
        print("No specific angle is in the common range")
        # Use a range of angles within the available data
        if common_min < common_max:
            valid_angles = np.linspace(common_min, common_max, 5).tolist()
            valid_angles = [round(a) for a in valid_angles]
        else:
            print("Cannot create comparison table: empty common range")
            return None
    
    print(f"Using angles: {valid_angles}")
    
    # Prepare tables for AP and IS
    ap_data = {"Abduction angle": [f"{angle}°" for angle in valid_angles]}
    is_data = {"Abduction angle": [f"{angle}°" for angle in valid_angles]}
    
    # Interpolate data for each type
    for type_name in sorted(type_data.keys()):
        data = type_data[type_name]
        if data is not None:
            # Use the exact case name
            display_name = type_name if type_name != 'Reference' else 'Ref'
            
            # Interpolation of AP and IS data
            ap_values = np.interp(valid_angles, data['abduction'], data['AP'])
            is_values = np.interp(valid_angles, data['abduction'], data['IS'])
            
            # Add to AP table
            ap_data[display_name] = [f"{val:.2f}" for val in ap_values]
            
            # Add to IS table
            is_data[display_name] = [f"{val:.2f}" for val in is_values]
    
    # Create DataFrames
    ap_df = pd.DataFrame(ap_data)
    is_df = pd.DataFrame(is_data)
    
    print("\nTable of AP translation values:")
    print(ap_df.to_string(index=False))
    
    print("\nTable of IS translation values:")
    print(is_df.to_string(index=False))
    
    return ap_df, is_df

# Function to create an AP-IS trajectory plot for a specific type compared to the reference
def create_individual_type_trajectory_plot(type_name, type_data, type_cases, reference_data=None):
    """
    Creates a graph comparing a specific type with the reference
    
    Args:
        type_name: The type name (exact case name)
        type_data: The type data
        type_cases: Dictionary of cases for each type
        reference_data: The reference data
    """
    if type_data is None:
        print(f"No data for {type_name}")
        return
    
    plt.figure(figsize=(10, 8))
    
    # Define graph limits
    plt.xlim(-2.5, 2.5)
    plt.ylim(-1.5, 7.5)
    
    # Add lines to divide quadrants
    plt.axhline(y=0, color='gray', linestyle='-', alpha=0.7, linewidth=1)
    plt.axvline(x=0, color='gray', linestyle='-', alpha=0.7, linewidth=1)
    
    # Color the quadrants
    plt.fill_between([-2.5, 0], 0, 7.5, color='lightblue', alpha=0.15)  # Posterior-Superior
    plt.fill_between([0, 2.5], 0, 7.5, color='lightgreen', alpha=0.15)  # Anterior-Superior
    plt.fill_between([-2.5, 0], -1.5, 0, color='lightcoral', alpha=0.15)  # Posterior-Inferior
    plt.fill_between([0, 2.5], -1.5, 0, color='lightyellow', alpha=0.15)  # Anterior-Inferior
    
    # Add annotations for quadrants
    plt.annotate('POSTERIOR-SUPERIOR', xy=(-1.25, 6), fontsize=10, ha='center', va='center', color='darkblue')
    plt.annotate('ANTERIOR-SUPERIOR', xy=(1.25, 6), fontsize=10, ha='center', va='center', color='darkgreen')
    plt.annotate('POSTERIOR-INFERIOR', xy=(-1.25, -0.75), fontsize=10, ha='center', va='center', color='darkred')
    plt.annotate('ANTERIOR-INFERIOR', xy=(1.25, -0.75), fontsize=10, ha='center', va='center', color='darkorange')
    
    # Plot the specific type data
    ap_data = type_data['AP']
    is_data = type_data['IS']
    angles = type_data['abduction']
    color = type_colors[type_name]
    
    # Use the exact case name
    type_label = type_name if type_name != 'Reference' else 'Reference'
    
    # Plot the main line
    plt.plot(ap_data, is_data, '-', color=color, linewidth=2, label=type_label)
    
    # Add specific angle points with annotations
    key_angles = [10, 120]
    for angle in key_angles:
        if min(angles) <= angle <= max(angles):
            idx = np.abs(np.array(angles) - angle).argmin()
            plt.plot(ap_data[idx], is_data[idx], 'o', color=color, markersize=8)
            plt.annotate(f"{angles[idx]:.0f}°", 
                         xy=(ap_data[idx], is_data[idx]), 
                         xytext=(5, 5),
                         textcoords='offset points',
                         fontsize=8)
    
    # Highlight the first point 
    plt.plot(ap_data[0], is_data[0], 'o', color='lime', markersize=10, markeredgecolor=color, markeredgewidth=2)
    plt.annotate(f"{angles[0]:.0f}°", 
                 xy=(ap_data[0], is_data[0]), 
                 xytext=(5, 5),
                 textcoords='offset points',
                 fontsize=8)
    
    # Highlight the last point
    plt.plot(ap_data[-1], is_data[-1], 'o', color='red', markersize=10, markeredgecolor=color, markeredgewidth=2)
    plt.annotate(f"{angles[-1]:.0f}°", 
                 xy=(ap_data[-1], is_data[-1]), 
                 xytext=(5, 5),
                 textcoords='offset points',
                 fontsize=8)
    
    # Add reference if it exists
    if reference_data is not None:
        ref_ap = reference_data['AP']
        ref_is = reference_data['IS']
        ref_angles = reference_data['abduction']
        
        # Plot the reference line
        plt.plot(ref_ap, ref_is, '--', color='black', linewidth=1.5, label='Reference')
        
        # Add some reference angle points
        for angle in key_angles:
            if min(ref_angles) <= angle <= max(ref_angles):
                idx = np.abs(np.array(ref_angles) - angle).argmin()
                plt.plot(ref_ap[idx], ref_is[idx], 's', color='black', markersize=6)
    
    # Configure titles and legends
    plt.title(f"AP-IS Translation Trajectory for {type_label}", fontsize=14)
    plt.xlabel('AP Translation (mm)\nNegative = Posterior, Positive = Anterior', fontsize=12)
    plt.ylabel('IS Translation (mm)\nNegative = Inferior, Positive = Superior', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(fontsize=10, loc='upper left')
    
    # Add a legend for start and end markers
    plt.plot([], [], 'o', color='lime', markersize=10, markeredgecolor='black', markeredgewidth=2, label='Start')
    plt.plot([], [], 'o', color='red', markersize=10, markeredgecolor='black', markeredgewidth=2, label='End')
    plt.legend(fontsize=10, loc='upper left')
    
    # Add a reference line at (0,0)
    plt.plot(0, 0, '+', color='black', markersize=12)
    plt.annotate('Origin (0,0)', xy=(0, 0), xytext=(0.2, -0.4), color='black', fontsize=8)
    
    # Improve readability
    plt.tight_layout()
    plt.show()

# Function to generate all individual graphs
def generate_all_individual_graphs(type_data, type_cases):
    """
    Generates all individual graphs for each type
    
    Args:
        type_data: Dictionary with data for each type
        type_cases: Dictionary of cases for each type
    """
    # Get reference data if it exists
    reference_data = type_data.get('Reference')
    
    # For each type (except reference), create graphs
    for type_name in type_data:
        if type_name != 'Reference' and type_data[type_name] is not None:
            print(f"Creating graphs for {type_name}...")
            create_individual_type_trajectory_plot(type_name, type_data[type_name], type_cases, reference_data)
    
    print("All individual graphs have been generated.")

# Function to generate improved graphs for all types
def generate_all_improved_graphs(type_data, type_cases):
    """
    Generates improved graphs for each type
    
    Args:
        type_data: Dictionary with data for each type
        type_cases: Dictionary of cases for each type
    """
    # Get reference data if it exists
    reference_data = type_data.get('Reference')
    
    # For each type (except reference), create improved graphs
    for type_name in type_data:
        if type_name != 'Reference' and type_data[type_name] is not None:
            print(f"Creating improved graphs for {type_name}...")
            create_improved_ap_is_graphs(type_name, type_data[type_name], reference_data)
    
    print("All improved graphs have been generated.")


# Function to explore a specific case
def explore_case(case_name):
    if case_name not in Results:
        print(f"Case {case_name} does not exist.")
        return
    
    print(f"\nDetailed exploration of case {case_name}:")
    print("Main keys:")
    for key in Results[case_name]:
        print(f"- {key}")
    
    # Specifically explore Abduction and HHT
    if 'Abduction' in Results[case_name]:
        print("\nKeys in Abduction:")
        for key in Results[case_name]['Abduction']:
            if isinstance(Results[case_name]['Abduction'][key], (list, np.ndarray)):
                arr = Results[case_name]['Abduction'][key]
                print(f"  - {key}: {type(arr)} with {len(arr)} values")
                if len(arr) > 0:
                    print(f"    First element: {arr[0]} ({type(arr[0])})")
    
    if 'HHT' in Results[case_name]:
        print("\nKeys in HHT:")
        for key in Results[case_name]['HHT']:
            if isinstance(Results[case_name]['HHT'][key], (list, np.ndarray)):
                arr = Results[case_name]['HHT'][key]
                print(f"  - {key}: {type(arr)} with {len(arr)} values")
                if len(arr) > 0:
                    print(f"    First element: {arr[0]} ({type(arr[0])})")
                    
 # Function to extract numeric data from a case
def extract_numeric_data(case_name):
     data = {'abduction': [], 'AP': [], 'IS': []}
     
     if case_name not in Results:
         print(f"Case {case_name} does not exist in the data.")
         return None
     
     # Check if necessary keys exist
     if 'Abduction' not in Results[case_name] or 'HHT' not in Results[case_name]:
         print(f"Abduction or HHT missing in {case_name}")
         return None
     
     # Find numeric abduction values
     abduction_found = False
     for key, value in Results[case_name]['Abduction'].items():
         if isinstance(value, (list, np.ndarray)):
             # Check that values are numeric
             numeric_values = []
             for val in value:
                 try:
                     if val is not None and val != 'Total':
                         numeric_values.append(float(val))
                 except (ValueError, TypeError):
                     pass  # Ignore non-numeric values
             
             if numeric_values:
                 data['abduction'] = numeric_values
                 abduction_found = True
                 print(f"Abduction: Found {len(numeric_values)} numeric values under key '{key}' for {case_name}")
                 break
     
     # Find AP values
     ap_found = False
     if 'AP' in Results[case_name]['HHT']:
         # Check that values are numeric
         numeric_values = []
         for val in Results[case_name]['HHT']['AP']:
             try:
                 if val is not None and val != 'Total':
                     numeric_values.append(float(val))
             except (ValueError, TypeError):
                 pass  # Ignore non-numeric values
         
         if numeric_values:
             data['AP'] = numeric_values
             ap_found = True
             print(f"AP: Found {len(numeric_values)} numeric values for {case_name}")
     
     # Find IS values
     is_found = False
     if 'IS' in Results[case_name]['HHT']:
         # Check that values are numeric
         numeric_values = []
         for val in Results[case_name]['HHT']['IS']:
             try:
                 if val is not None and val != 'Total':
                     numeric_values.append(float(val))
             except (ValueError, TypeError):
                 pass  # Ignore non-numeric values
         
         if numeric_values:
             data['IS'] = numeric_values
             is_found = True
             print(f"IS: Found {len(numeric_values)} numeric values for {case_name}")
     
     # Check that all data has been found
     if not (abduction_found and ap_found and is_found):
         print(f"Incomplete data for {case_name}")
         return None
     
     # Check that all lists have the same length
     min_length = min(len(data['abduction']), len(data['AP']), len(data['IS']))
     if min_length < max(len(data['abduction']), len(data['AP']), len(data['IS'])):
         print(f"Different lengths for {case_name}, truncating to {min_length}")
         data['abduction'] = data['abduction'][:min_length]
         data['AP'] = data['AP'][:min_length]
         data['IS'] = data['IS'][:min_length]
     
     return data        
                    
# Fonction main() modifiée
def main():
    # Identifier les cas disponibles avec leurs noms réels
    type_cases = identify_case_types()
    
    if not type_cases:
        print("Aucun cas identifié.")
        return
    
    # Générer les couleurs pour chaque type
    global type_colors
    type_colors = get_type_colors(type_cases)
    
    # Explorer chaque cas identifié
    for type_name, case_name in type_cases.items():
        if case_name:
            explore_case(case_name)
    
    # Extraire les données pour chaque type
    type_data = {}
    for type_name, case_name in type_cases.items():
        if case_name:
            type_data[type_name] = extract_numeric_data(case_name)
    
    # Vérifier si au moins un type a des données
    has_data = any(data is not None for data in type_data.values())
    if not has_data:
        print("Aucune donnée valide n'a pu être extraite.")
        return
    
    # Créer le graphique de trajectoire pour tous les types
    create_all_types_trajectory_plot(type_data, type_cases)
    
    # Créer le tableau de comparaison pour tous les types
    create_all_types_comparison_table(type_data, type_cases)
    
    # Générer les graphiques individuels pour chaque type
    # generate_all_individual_graphs(type_data, type_cases)
    
    # Générer les graphiques améliorés pour chaque type
    generate_all_improved_graphs(type_data, type_cases)
    
    print("Analyse terminée.")
       
# Exécuter le programme principal
if __name__ == "__main__":
    main()           

