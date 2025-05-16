import os
os.chdir(r"C:\Users\Documents\Python")
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


# %% Control the font size for graphs
matplotlib.rcParams.update({'font.size': 14})
matplotlib.rcParams.update({'axes.titlesize': 14})
matplotlib.rcParams.update({'figure.titlesize': 14})
matplotlib.rcParams.update({'axes.labelsize': 14})
matplotlib.rcParams.update({'xtick.labelsize': 14})
matplotlib.rcParams.update({'ytick.labelsize': 14})
matplotlib.rcParams.update({'legend.fontsize': 14})

# %% Load results
SaveSimulationsDirectory = "C:/Users/Documents/Python/Saved Simulations"
Results = load_results_from_file(SaveSimulationsDirectory, "Results")

# %% List of muscle categories
Muscles_Main = [
    "Deltoideus anterior",
    "Deltoideus lateral",
    "Deltoideus posterior",
    "Infraspinatus",
    "Supraspinatus",
    "Subscapularis",
    # "Teres minor",
    "Lower trapezius",
    "Middle trapezius",
    "Upper trapezius",
    # "Biceps brachii long head",
    # "Biceps brachii short head",
  
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
    try:
        abduction_angles = results[case_name]['Abduction']['Total']
        print(f"Processing case: {case_name}")
        print(f"Number of abduction data points: {len(abduction_angles)}")
        print(f"Range of abduction angles: {min(abduction_angles)} to {max(abduction_angles)} degrees")
    except KeyError as e:
        print(f"Error accessing abduction data for {case_name}: {e}")
        # Initialize with empty data
        abduction_angles = []
    
    # Process each muscle
    for muscle in muscles:
        case_data[muscle] = []
        
        try:
            # Get muscle force data
            force_data = results[case_name]["Muscles"][muscle][muscle]["Ft"]["Total"]
            
            # Check if lengths match
            if len(force_data) != len(abduction_angles):
                print(f"Warning: Length mismatch for {muscle} - Angles: {len(abduction_angles)}, Forces: {len(force_data)}")
                case_data[muscle] = [0.0] * len(angle_ranges)  # Use 0.0 instead of NaN
                continue
                
            # Calculate average force for each angle interval
            for start_angle, end_angle in angle_ranges:
                # Find indices of angles in the defined range
                indices = [i for i, angle in enumerate(abduction_angles) 
                           if start_angle <= angle <= end_angle]
                
                if not indices:
                    print(f"  Warning: No data for {muscle} between {start_angle}° and {end_angle}°")
                    case_data[muscle].append(0.0)  # Use 0.0 instead of NaN
                    continue
                
                # Calculate the average force over the interval
                range_forces = [force_data[i] for i in indices]
                avg_force = np.mean(range_forces)
                case_data[muscle].append(avg_force)
                
        except KeyError as e:
            print(f"Error accessing data for {muscle}: {e}")
            case_data[muscle] = [0.0] * len(angle_ranges)  # Use 0.0 instead of NaN
    
    return case_data

# %% Calculation of percentage differences - MODIFIED
def calculate_percentage_diff(ref_data, comp_data, muscles, angle_ranges):
    """
    Calculates percentage differences between the reference case and a comparison case
    
    Args:
        ref_data: Reference case data
        comp_data: Comparison case data
        muscles: List of muscles
        angle_ranges: List of angle intervals
        
    Returns:
        tuple: (percentage_diff, activity_status) - Percentage differences and activity status for cells
    """
    percentage_diff = {}
    activity_status = {}  # Status for each cell and overall muscle
    
    for muscle in muscles:
        percentage_diff[muscle] = []
        activity_status[muscle] = []  # Status for each cell
        
        # Check if the muscle is completely inactive (all comparison values are 0)
        all_comp_zero = True
        for i in range(len(angle_ranges)):
            comp_val = comp_data[muscle][i] if i < len(comp_data[muscle]) else 0.0
            if np.isnan(comp_val):
                comp_val = 0.0
            if abs(comp_val) >= 0.001:
                all_comp_zero = False
                break
        
        # Process each angle range
        for i in range(len(angle_ranges)):
            ref_val = ref_data[muscle][i] if i < len(ref_data[muscle]) else 0.0
            comp_val = comp_data[muscle][i] if i < len(comp_data[muscle]) else 0.0
            
            # Handle NaN values by converting to 0.0
            if np.isnan(ref_val):
                ref_val = 0.0
            if np.isnan(comp_val):
                comp_val = 0.0
            
            # If entire muscle is inactive, mark all cells as "muscle_inactive"
            if all_comp_zero:
                percentage_diff[muscle].append(0.0)
                activity_status[muscle].append("muscle_inactive")
                continue
            
            # Both values are effectively zero
            if abs(ref_val) < 0.001 and abs(comp_val) < 0.001:
                percentage_diff[muscle].append(0.0)  # Just say 0% difference
                activity_status[muscle].append("zero")
            
            # Reference is effectively zero but comp is not
            elif abs(ref_val) < 0.001 and abs(comp_val) >= 0.001:
                # Use a fixed high percentage value rather than infinity
                percentage_diff[muscle].append(999.9)  # Use a high value for percentage difference
                activity_status[muscle].append("normal")
            
            # Reference is not zero but comp is effectively zero
            elif abs(ref_val) >= 0.001 and abs(comp_val) < 0.001:
                percentage_diff[muscle].append(-100.0)  # -100% change
                activity_status[muscle].append("zero")
            
            # Both non-zero - standard percentage calculation
            else:
                pct_diff = ((comp_val - ref_val) / ref_val) * 100
                percentage_diff[muscle].append(pct_diff)
                activity_status[muscle].append("normal")
    
    return percentage_diff, activity_status

# %% Creation of percentage difference graph - MODIFIED
def create_percentage_diff_heatmap(percentage_diff, activity_status, ref_case, comp_case, angle_ranges, muscles, ref_data, comp_data):
    """
    Creates a heatmap of percentage differences between two cases
    
    Args:
        percentage_diff: Dictionary of percentage differences
        activity_status: Dictionary of activity status for cells
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
    
    # Cap extreme values for visualization
    df_diff = df_diff.clip(lower=-100, upper=1000)
    
    # Create a version for textual display of percentages with average values in Newton
    df_display = pd.DataFrame(index=df_diff.index, columns=df_diff.columns, dtype=object)
    df_display = df_display.fillna("")
    
    # Keep track of completely inactive muscles
    inactive_muscles = set()
    
    # Format percentages for display and add values in Newton
    for muscle in muscles:
        # Check if muscle is completely inactive
        all_inactive = False
        for i, col in enumerate(columns):
            status = activity_status[muscle][i]
            if status == "muscle_inactive":
                inactive_muscles.add(muscle)
                all_inactive = True
                break
            
        for i, col in enumerate(columns):
            # Get values in Newton and ensure they're not NaN
            ref_val = ref_data[muscle][i] if i < len(ref_data[muscle]) else 0.0
            comp_val = comp_data[muscle][i] if i < len(comp_data[muscle]) else 0.0
            if np.isnan(ref_val): ref_val = 0.0
            if np.isnan(comp_val): comp_val = 0.0
            
            status = activity_status[muscle][i]
            diff_val = percentage_diff[muscle][i]
            
            # Format based on status
            if status == "muscle_inactive":
                df_display.loc[muscle, col] = f"Inactive\n({ref_val:.1f}N / {comp_val:.1f}N)"
            elif status == "zero":
                # Just display 0% for zero values
                df_display.loc[muscle, col] = f"0.0%\n({ref_val:.1f}N / {comp_val:.1f}N)"
            elif status == "normal":
                # For very high values, cap the displayed percentage
                if diff_val > 999:
                    df_display.loc[muscle, col] = f">999%\n({ref_val:.1f}N / {comp_val:.1f}N)"
                else:
                    df_display.loc[muscle, col] = f"{diff_val:.2f}%\n({ref_val:.1f}N / {comp_val:.1f}N)"
            else:
                # Fallback for unexpected status
                df_display.loc[muscle, col] = f"??\n({ref_val:.1f}N / {comp_val:.1f}N)"
    
    # Create the figure
    plt.figure(figsize=(14, 10))  # Increase size to accommodate more text
    
    # Create the main heatmap of percentages
    ax = sns.heatmap(df_diff, 
                     annot=df_display, 
                     fmt="", 
                     cmap="RdYlGn", 
                     center=0, 
                     linewidths=0.5,
                     cbar_kws={'label': 'Difference in %'},
                     vmin=-100,  # Minimum value for color scale
                     vmax=100)   # Maximum value for color scale - capped to make differences visible
    
    # Apply custom cell colors based on activity status
    # Get the dimensions of the heatmap
    num_rows, num_cols = len(muscles), len(columns)
    
    # Go through each cell
    for row_idx, muscle in enumerate(muscles):
        # If the entire muscle is inactive, shade the whole row
        if muscle in inactive_muscles:
            for col_idx in range(len(columns)):
                rect = plt.Rectangle(
                    (col_idx, row_idx),  # Position (x, y) of the bottom left corner
                    1, 1,                # Width and height of the rectangle
                    fill=True,
                    color='lightgrey',
                    alpha=0.5,           # Opacity
                    zorder=2             # Ensure the rectangle is above the heatmap
                )
                ax.add_patch(rect)
        else:
            # Otherwise, color individual cells based on their status
            for col_idx, col in enumerate(columns):
                status = activity_status[muscle][col_idx]
                if status == "zero":
                    # Lighter background for zero difference but active muscle
                    rect = plt.Rectangle(
                        (col_idx, row_idx),
                        1, 1,
                        fill=True,
                        color='lightyellow',  # Very light yellow for zero values
                        alpha=0.3,
                        zorder=2
                    )
                    ax.add_patch(rect)
    
    # Adjust axes
    plt.title(f"Percentage differences between {ref_case} and {comp_case}")
    plt.xlabel("Angle range (°)")
    plt.xticks(rotation=45)
    plt.ylabel("Muscles")
    plt.yticks(rotation=0)
    
    # Display the table
    plt.tight_layout()
    plt.show()
    
    return df_diff, activity_status

# %% Main function to generate all difference graphs
def generate_all_difference_graphs(muscles_to_analyze=None):
    """
    Generates a percentage difference graph for each case compared to the reference
    
    Args:
        muscles_to_analyze: List of muscles to analyze, or None to analyze all muscle categories
    """
    # If no specific muscle list provided, use all muscle categories
    if muscles_to_analyze is None:
        # Combine all muscle lists
        muscles_to_analyze = Muscles_Main + Muscles_Aux + Muscles_Extra
        # Remove duplicates while preserving order
        muscles_to_analyze = list(dict.fromkeys(muscles_to_analyze))
        print(f"Analyzing all {len(muscles_to_analyze)} muscles")
    
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
        percentage_diff, activity_status = calculate_percentage_diff(ref_data, comp_data, muscles_to_analyze, angle_ranges)
        
        # Create and display the heatmap with data in Newton
        df_numeric, df_status = create_percentage_diff_heatmap(
            percentage_diff, activity_status, ref_case, comp_case, angle_ranges, muscles_to_analyze, ref_data, comp_data
        )
        
        # Optionally, print a table of fully inactive muscles
        inactive_muscles = [muscle for muscle in muscles_to_analyze 
                           if all(status == "muscle_inactive" for status in activity_status[muscle])]
        
        if inactive_muscles:
            print(f"\nInactive muscles in {comp_case} ({len(inactive_muscles)}):")
            for muscle in inactive_muscles:
                print(f"  - {muscle}")
        
        print(f"Difference graph created for {comp_case}")
    
    print("\nAll difference graphs have been generated.")   
    

# %% Main execution
if __name__ == "__main__":
    # Pour analyser tous les muscles en une seule fois
    # generate_all_difference_graphs()
    
    # Si vous préférez analyser les muscles par catégorie, décommentez les lignes suivantes
    generate_all_difference_graphs(Muscles_Main)
    generate_all_difference_graphs(Muscles_Aux)
    generate_all_difference_graphs(Muscles_Extra)
