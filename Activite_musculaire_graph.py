import os
os.chdir(r"C:\Users\p0137717\Documents\Python")
import pandas as pd
import numpy as np
import seaborn as sns  
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
    """
    Load simulation results with the option to use a specific selection file.
    If a selection file is specified, it uses that; otherwise, it loads the default results.
    
    Returns:
        The loaded simulation results
    """
    import pickle
    import os
    
    # Directory for saved simulations
    SaveSimulationsDirectory = "C:/Users/p0137717/Documents/Python/Saved Simulations"
    
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


# %% Control the font size for graphs
matplotlib.rcParams.update({'font.size': 14})
matplotlib.rcParams.update({'axes.titlesize': 14})
matplotlib.rcParams.update({'figure.titlesize': 14})
matplotlib.rcParams.update({'axes.labelsize': 14})
matplotlib.rcParams.update({'xtick.labelsize': 14})
matplotlib.rcParams.update({'ytick.labelsize': 14})
matplotlib.rcParams.update({'legend.fontsize': 14})

# %% Load results
SaveSimulationsDirectory = "C:/Users/p0137717/Documents/Python/Saved Simulations"
Results = load_results_from_file(SaveSimulationsDirectory, "Results")

# %% List of muscle categories
Muscles_Main = [
    "Deltoideus anterior",
    "Deltoideus lateral",
    "Deltoideus posterior",
    "Infraspinatus",
    "Supraspinatus",
    "Subscapularis",
    "Teres minor",
    "Lower trapezius",
    "Middle trapezius",
    "Upper trapezius",
    # "Biceps brachii long head",
    # "Biceps brachii short head",
    # # "Triceps long head",
    # "Pectoralis major clavicular",
    # "Pectoralis major clavicular",
    # "Pectoralis major sternal",
    # "Pectoralis minor",
]

Muscles_Aux = [
    "Pectoralis major clavicular",
    "Pectoralis major sternal",
    "Pectoralis minor",
    "Teres major",
    "Teres minor",
    "Rhomboideus",
    "Serratus anterior",
    "Biceps brachii long head",
    "Biceps brachii short head"
]

Muscles_Extra = [
    "Sternocleidomastoid sternum",
    "Sternocleidomastoid clavicular",
    "Latissimus dorsi",
    "Levator scapulae",
    "Coracobrachialis",
    "Triceps long head",
]

# %% Identification of reference case and all cases to compare
def identify_reference_and_compare_cases(results):
    """
    Automatically identifies the reference case and all cases to compare
    
    Returns:
        tuple: (ref_case, compare_cases)
    """
    available_cases = list(results.keys())
    
    if not available_cases:
        print("No available cases in the data")
        return None, []
    
    print("\nAvailable cases in the data:")
    for i, case_name in enumerate(available_cases):
        print(f"{i+1}. {case_name}")
    
    # Automatically identify the reference
    reference_pattern = r'ref|reference'
    ref_case = None
    for case_name in available_cases:
        if re.search(reference_pattern, case_name, re.IGNORECASE):
            ref_case = case_name
            print(f"Reference case identified: {case_name}")
            break
    
    # If no reference is found, use the first case
    if ref_case is None and available_cases:
        ref_case = available_cases[0]
        print(f"No explicit reference case found, using the first case as reference: {ref_case}")
    
    # Identify all cases to compare (different from the reference)
    compare_cases = [case for case in available_cases if case != ref_case]
    
    if compare_cases:
        print(f"Cases to compare identified ({len(compare_cases)}):")
        for case in compare_cases:
            print(f"  - {case}")
    else:
        print("Warning: No cases to compare are available")
    
    return ref_case, compare_cases

# %% Data extraction for a case
def extract_case_data(results, case_name, muscles, angle_ranges):
    """
    Extracts the average force data for each angle interval for a case
    
    Args:
        results: Loaded results
        case_name: Case name
        muscles: List of muscles to analyze
        angle_ranges: List of angle intervals
        
    Returns:
        dict: Muscle data
    """
    case_data = {}
    
    # Get abduction angles
    abduction_angles = results[case_name]['Abduction']['Total']
    print(f"Processing case: {case_name}")
    print(f"Number of abduction data points: {len(abduction_angles)}")
    print(f"Range of abduction angles: {min(abduction_angles)} to {max(abduction_angles)} degrees")
    
    # Process each muscle
    for muscle in muscles:
        case_data[muscle] = []
        
        try:
            # Get muscle force data
            force_data = results[case_name]["Muscles"][muscle][muscle]["Ft"]["Total"]
            
            # Check if lengths match
            if len(force_data) != len(abduction_angles):
                print(f"Warning: Length mismatch for {muscle} - Angles: {len(abduction_angles)}, Forces: {len(force_data)}")
                case_data[muscle] = [float('nan')] * len(angle_ranges)
                continue
                
            # Calculate average force for each angle interval
            for start_angle, end_angle in angle_ranges:
                # Find indices of angles in the defined range
                indices = [i for i, angle in enumerate(abduction_angles) 
                           if start_angle <= angle <= end_angle]
                
                if not indices:
                    print(f"  Warning: No data for {muscle} between {start_angle}° and {end_angle}°")
                    case_data[muscle].append(float('nan'))
                    continue
                
                # Calculate the average force over the interval
                range_forces = [force_data[i] for i in indices]
                avg_force = np.mean(range_forces)
                case_data[muscle].append(avg_force)
                
        except KeyError as e:
            print(f"Error accessing data for {muscle}: {e}")
            case_data[muscle] = [float('nan')] * len(angle_ranges)
    
    return case_data

# %% Calculation of percentage differences
def calculate_percentage_diff(ref_data, comp_data, muscles, angle_ranges):
    """
    Calculates percentage differences between the reference case and a comparison case
    
    Args:
        ref_data: Reference case data
        comp_data: Comparison case data
        muscles: List of muscles
        angle_ranges: List of angle intervals
        
    Returns:
        tuple: (percentage_diff, inactive_mask) - Percentage differences and mask for inactive cells
    """
    percentage_diff = {}
    inactive_mask = {}  # Mask for inactive cells
    
    for muscle in muscles:
        percentage_diff[muscle] = []
        inactive_mask[muscle] = []  # 1:1 correspondence with percentage_diff
        
        for i in range(len(angle_ranges)):
            ref_val = ref_data[muscle][i] if i < len(ref_data[muscle]) else float('nan')
            comp_val = comp_data[muscle][i] if i < len(comp_data[muscle]) else float('nan')
            
            # By default, the cell is not inactive
            is_inactive = False
            
            if np.isnan(ref_val) or np.isnan(comp_val) or abs(ref_val) < 0.001:
                # If NaN values or reference close to zero, we can't calculate percentage
                percentage_diff[muscle].append(float('nan'))
            else:
                pct_diff = ((comp_val - ref_val) / ref_val) * 100
                
                # Check if inactive (comp_val close to 0 or difference very close to -100%)
                if abs(comp_val) < 0.001 and abs(ref_val) >= 0.001:
                    is_inactive = True
                    percentage_diff[muscle].append(float('nan'))  # NaN will be masked in the heatmap
                elif pct_diff <= -99.9:
                    is_inactive = True
                    percentage_diff[muscle].append(float('nan'))  # NaN will be masked in the heatmap
                else:
                    percentage_diff[muscle].append(pct_diff)
            
            # Record inactivity status
            inactive_mask[muscle].append(is_inactive)
    
    return percentage_diff, inactive_mask

# %% Creation of percentage difference graph
def create_percentage_diff_heatmap(percentage_diff, inactive_mask, ref_case, comp_case, angle_ranges, muscles, ref_data, comp_data):
    """
    Creates a heatmap of percentage differences between two cases
    
    Args:
        percentage_diff: Dictionary of percentage differences
        inactive_mask: Dictionary of masks for inactive cells
        ref_case: Reference case name
        comp_case: Comparison case name
        angle_ranges: List of angle intervals
        muscles: List of muscles
        ref_data: Reference case data
        comp_data: Comparison case data
    """
    # Create columns for DataFrames
    columns = [f"{start}-{end}°" for start, end in angle_ranges]
    
    # Create a DataFrame for coloring
    df_diff = pd.DataFrame.from_dict(percentage_diff, orient='index', columns=columns)
    
    # Create a DataFrame for the inactivity mask
    df_inactive = pd.DataFrame.from_dict(inactive_mask, orient='index', columns=columns)
    
    # Create a version for textual display of percentages with average values in Newton
    df_display = df_diff.copy()
    
    # Format percentages for display and add values in Newton
    for muscle in muscles:
        for i, col in enumerate(columns):
            if not pd.isna(df_display.loc[muscle, col]):
                # Get values in Newton
                ref_val = ref_data[muscle][i]
                comp_val = comp_data[muscle][i]
                # Format display: %diff (ref_val N / comp_val N)
                df_display.loc[muscle, col] = f"{df_display.loc[muscle, col]:.1f}%\n({ref_val:.1f}N / {comp_val:.1f}N)"
            else:
                df_display.loc[muscle, col] = ""
    
    # Create the figure
    plt.figure(figsize=(14, 10))  # Increase size to accommodate more text
    
    # Create the main heatmap of percentages
    ax = sns.heatmap(df_diff, 
                    annot=df_display, 
                    fmt="", 
                    cmap="RdYlGn", 
                    center=0, 
                    linewidths=0.5,
                    cbar_kws={'label': 'Difference in %'})
    
    # Now we'll draw gray rectangles for inactive cells
    # and add the text "Inactive" on these rectangles
    
    # Get the dimensions of the heatmap
    num_rows, num_cols = df_inactive.shape
    
    # Go through each cell
    for row_idx in range(num_rows):
        for col_idx in range(num_cols):
            # If the cell is marked as inactive
            if df_inactive.iloc[row_idx, col_idx]:
                # Create a gray rectangle for the cell
                rect = plt.Rectangle(
                    (col_idx, row_idx),  # Position (x, y) of the bottom left corner
                    1, 1,                # Width and height of the rectangle
                    fill=True,
                    color='lightgrey',
                    alpha=0.8,           # Opacity
                    zorder=2             # Ensure the rectangle is above the heatmap
                )
                ax.add_patch(rect)
                
                # Simply add the text "Inactive" in the center of the cell without Newton values
                ax.text(
                    col_idx + 0.5,       # x position (center of cell)
                    row_idx + 0.5,       # y position (center of cell)
                    "Inactive",          # Text without values
                    horizontalalignment='center',
                    verticalalignment='center',
                    fontweight='bold',
                    color='black',
                    zorder=3             # Ensure the text is above the rectangle
                )
    
    # Adjust axes
    plt.title(f"Percentage differences between {ref_case} and {comp_case}")
    plt.xlabel("Angle range (°)")
    plt.xticks(rotation=45)
    plt.ylabel("Muscles")
    plt.yticks(rotation=0)
    
    # Display the table
    plt.tight_layout()
    # plt.savefig(f"differences_{ref_case}_vs_{comp_case}.png", dpi=300, bbox_inches='tight')
    plt.show()
    
    return df_diff, df_inactive

# %% Main function to generate all difference graphs
def generate_all_difference_graphs(muscles_to_analyze=Muscles_Main):
    """
    Generates a percentage difference graph for each case compared to the reference
    
    Args:
        muscles_to_analyze: List of muscles to analyze
    """
    # Definition of angle intervals
    angle_ranges = [
        (10, 30),
        (30, 60),
        (60, 90),
        (90, 120)
    ]
    
    # Identify the reference and cases to compare
    ref_case, compare_cases = identify_reference_and_compare_cases(Results)
    
    if not ref_case:
        print("Cannot continue analysis without a reference case.")
        return
    
    if not compare_cases:
        print("No cases to compare with the reference.")
        return
    
    # Extract reference data
    ref_data = extract_case_data(Results, ref_case, muscles_to_analyze, angle_ranges)
    
    # For each case to compare, generate a graph
    for comp_case in compare_cases:
        print(f"\nComparative analysis: {ref_case} vs {comp_case}")
        
        # Extract data for the case to compare
        comp_data = extract_case_data(Results, comp_case, muscles_to_analyze, angle_ranges)
        
        # Calculate percentage differences
        percentage_diff, inactive_mask = calculate_percentage_diff(ref_data, comp_data, muscles_to_analyze, angle_ranges)
        
        # Create and display the heatmap with data in Newton
        df_numeric, df_inactive = create_percentage_diff_heatmap(
            percentage_diff, inactive_mask, ref_case, comp_case, angle_ranges, muscles_to_analyze, ref_data, comp_data
        )
        
        print(f"Difference graph created for {comp_case}")
    
    print("\nAll difference graphs have been generated.")    

# %% Main execution
if __name__ == "__main__":
    # Display standard muscle graphs
    # #Total muscle forces
    # PremadeGraphs.muscle_graph_from_list(Results, Muscles_Main, [3, 5], "Abduction", "Ft","Main muscles: Total muscle forces", cases_on="all", composante_y=["Total"],hide_center_axis_labels=True)
    # PremadeGraphs.muscle_graph_from_list(Results, Muscles_Aux, [3, 3], "Abduction", "Ft", "Auxiliary muscles: Total muscle forces", cases_on="all", composante_y=["Total"], hide_center_axis_labels=True, same_lim=True)
    # PremadeGraphs.muscle_graph_from_list(Results, Muscles_Extra, [2, 3], "Abduction", "Ft", "Extra muscles: Total muscle forces", cases_on="all", composante_y=["Total"], hide_center_axis_labels=True, same_lim=True)
    
    # Generate percentage difference graphs
    generate_all_difference_graphs(Muscles_Main)
    # generate_all_difference_graphs(Muscles_Aux)