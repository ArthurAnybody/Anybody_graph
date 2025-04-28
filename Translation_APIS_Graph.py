import os
os.chdir(r"C:\Users\Documents\Python")
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

# Modified function for loading results
def _load_results_with_selection():
    import pickle
    import os
    
    # Directory for saved simulations
    SaveSimulationsDirectory = "C:/Users/Documents/Python/Saved Simulations"
    
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
SaveSimulationsDirectory = "C:/Users/Documents/Python/Saved Simulations"

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
    reference_pattern = r'ref|reference|AnyBody Parameters'
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

# Update colors to work with dynamic names
def get_type_colors(type_cases):
    # Color palette for different types
    color_palette = [
        '#1f77b4',  # blue
        '#ff7f0e',  # orange
        '#2ca02c',  # green
        '#d62728',  # red
        '#9467bd',  # purple
        '#8c564b',  # brown
        '#e377c2',  # pink
        '#7f7f7f',  # gray
        '#bcbd22',  # yellow-green
        '#17becf'   # cyan
    ]
    
    type_colors = {}
    
    # Always assign black to the reference if it exists
    if 'Reference' in type_cases:
        type_colors['Reference'] = 'black'
    
    # Assign colors to each type
    color_index = 0
    for type_name in type_cases:
        if type_name != 'Reference' and type_name not in type_colors:
            type_colors[type_name] = color_palette[color_index % len(color_palette)]
            color_index += 1
    
    return type_colors

# Modified function to create improved AP and IS graphs
def create_improved_ap_is_graphs(type_name, type_data, reference_data=None):
    """
    Creates improved graphs for AP and IS with subplots
    
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
    if reference_data is not None:
        reference_ap = reference_data['AP']
        reference_is = reference_data['IS']
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 16))
    
    # Configure AP (Anteroposterior) graph
    ax1.axhline(y=0, color='gray', linestyle='-', alpha=0.7, linewidth=1)
    min_angle = min(angles)
    max_angle = max(angles)
    ax1.fill_between([min_angle, max_angle], 0, 2.5, color='lightblue', alpha=0.3, label='Anterior Zone')
    ax1.fill_between([min_angle, max_angle], -2.5, 0, color='lightcoral', alpha=0.3, label='Posterior Zone')
    
    # Plot the type curve with the exact name
    type_label = type_name if type_name != 'Reference' else 'Reference'
    ax1.plot(angles, type_ap, 'o-', label=type_label, linewidth=2, markersize=8, color=type_colors[type_name])
    
    # Plot the reference curve if available
    if reference_ap is not None:
        ax1.plot(angles, reference_ap, '--', label='Reference', linewidth=2, color='black')
    
    # Add explanatory annotations
    ax1.annotate('ANTERIOR', xy=(max_angle * 0.9, 1), 
                fontsize=12, ha='center', va='center', color='darkblue')
    ax1.annotate('POSTERIOR', xy=(max_angle * 0.9, -1.5), 
                fontsize=12, ha='center', va='center', color='darkred')
    
    # Configure AP graph appearance
    ax1.set_title(f'AP (Anteroposterior) Translations - {type_label}', fontsize=18, fontweight='bold')
    ax1.set_xlabel("Abduction Angle (°)", fontsize=14)
    ax1.set_ylabel('AP Translation (mm)', fontsize=14)
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.legend(fontsize=12, loc='upper left')
    
    # Define tick marks for angles
    step = max(1, len(angles) // 10)  # Limit the number of tick marks
    ax1.set_xticks(angles[::step])
    ax1.set_xticklabels([f"{int(angle)}°" for angle in angles[::step]])
    ax1.set_ylim(-2.5, 2.5)
    
    # Configure IS (Inferosuperior) graph
    ax2.axhline(y=0, color='gray', linestyle='-', alpha=0.7, linewidth=1)
    ax2.fill_between([min_angle, max_angle], 0, 7.5, color='lightblue', alpha=0.3, label='Superior Zone')
    ax2.fill_between([min_angle, max_angle], -1.5, 0, color='lightcoral', alpha=0.3, label='Inferior Zone')
    
    # Plot the type curve
    ax2.plot(angles, type_is, 'o-', label=type_label, linewidth=2, markersize=8, color=type_colors[type_name])
    
    # Plot the reference curve if available
    if reference_is is not None:
        ax2.plot(angles, reference_is, '--', label='Reference', linewidth=2, color='black')
    
    # Add explanatory annotations for IS
    ax2.annotate('SUPERIOR', xy=(max_angle * 0.9, 4), 
                fontsize=12, ha='center', va='center', color='darkblue')
    ax2.annotate('INFERIOR', xy=(max_angle * 0.9, -1), 
                fontsize=12, ha='center', va='center', color='purple')
    
    # Configure IS graph appearance
    ax2.set_title(f'IS (Inferosuperior) Translations - {type_label}', fontsize=18, fontweight='bold')
    ax2.set_xlabel("Abduction angle (°)", fontsize=14)
    ax2.set_ylabel('IS Translation (mm)', fontsize=14)
    ax2.grid(True, linestyle='--', alpha=0.7)
    ax2.legend(fontsize=12, loc='upper left')
    
    # Define tick marks for angles
    ax2.set_xticks(angles[::step])
    ax2.set_xticklabels([f"{int(angle)}°" for angle in angles[::step]])
    ax2.set_ylim(-1.5, 7.5)
    
    # Adjust spacing
    plt.tight_layout(pad=4.0)
    plt.show()

# Function to create AP-IS trajectory plot for all types
def create_all_types_trajectory_plot(type_data, type_cases):
    plt.figure(figsize=(14, 12))

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

    # Function to plot a curve with special markers for first and last point
    def plot_type(type_name, data):
        if data is None:
            print(f"No data for {type_name}")
            return
        
        ap_data = data['AP']
        is_data = data['IS']
        angles = data['abduction']
        color = type_colors[type_name]
        
        # Use the exact case name as label
        label = type_name if type_name != 'Reference' else 'Reference'
        
        # Plot the main line
        plt.plot(ap_data, is_data, '-', color=color, linewidth=2, label=label)
        
        # Plot all intermediate points
        for i in range(1, len(angles)-1):
            plt.plot(ap_data[i], is_data[i], 'o', color=color, markersize=7)
        
        # Highlight the first point in green
        plt.plot(ap_data[0], is_data[0], 'o', color='lime', markersize=12, markeredgecolor=color, markeredgewidth=2)
        
        # Highlight the last point in red
        plt.plot(ap_data[-1], is_data[-1], 'o', color='red', markersize=12, markeredgecolor=color, markeredgewidth=2)

    # Plot all types
    for type_name in type_data:
        if type_data[type_name] is not None:
            plot_type(type_name, type_data[type_name])

    # Configure titles and legends
    plt.title('AP-IS Translation Trajectory', fontsize=16, fontweight='bold')
    plt.xlabel('AP Translation (mm)\nNegative = Posterior, Positive = Anterior', fontsize=12)
    plt.ylabel('IS Translation (mm)\nNegative = Inferior, Positive = Superior', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(fontsize=10, loc='upper left')

    # Add a legend for start and end markers
    plt.plot([], [], 'o', color='lime', markersize=12, markeredgecolor='black', markeredgewidth=2, label='Start')
    plt.plot([], [], 'o', color='red', markersize=12, markeredgecolor='black', markeredgewidth=2, label='End')
    plt.legend(fontsize=10, loc='upper left')

    # Add a reference line at (0,0)
    plt.plot(0, 0, '+', color='black', markersize=12)
    plt.annotate('Origin (0,0)', xy=(0, 0), xytext=(0.2, -0.4), color='black', fontsize=8)

    # Improve readability
    plt.tight_layout()
    plt.show()

# Function to create a comparison table for all types
def create_all_types_comparison_table(type_data, type_cases):
    # Define specific angles for the table
    specific_angles = [10, 20, 40, 50, 60, 70, 80, 90, 100, 110, 120]
    
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
    generate_all_individual_graphs(type_data, type_cases)
    
    # Générer les graphiques améliorés pour chaque type
    generate_all_improved_graphs(type_data, type_cases)
    
    print("Analyse terminée.")
       
# Exécuter le programme principal
if __name__ == "__main__":
    main()         
