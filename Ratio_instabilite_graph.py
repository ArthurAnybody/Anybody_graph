import os
os.chdir(r"C:\Users\p0137717\Documents\Python")

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
import pandas as pd
import numpy as np
import seaborn as sns  
import re


import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt

# Variable to store the path to a file with selected results
SELECTED_RESULTS_FILE = None

# Modified function for loading results
def _load_results_with_selection():
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

# %% Control the font size for graphs

# Control the global font size
matplotlib.rcParams.update({'font.size': 14})
# Control the sizes of each part of the graph
# Title of subplot boxes
matplotlib.rcParams.update({'axes.titlesize': 14})
# Graph title
matplotlib.rcParams.update({'figure.titlesize': 14})
# Axis names
matplotlib.rcParams.update({'axes.labelsize': 14})
# Axis tick labels
matplotlib.rcParams.update({'xtick.labelsize': 14})
matplotlib.rcParams.update({'ytick.labelsize': 14})
# Legend
matplotlib.rcParams.update({'legend.fontsize': 14})

# %% Automatically identify the reference and comparison cases
def identify_reference_and_compare_cases(results):
    """
    Automatically identifies the reference case and all cases to compare
    """
    available_cases = list(results.keys())
    
    if not available_cases:
        print("No cases available in the data")
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

# %% Calculate instability ratio for all cases
def calculate_instability_ratio(results):
    """
    Calculates the instability ratio for all cases
    """
    for case in results:
        # For Shear where we add IS and AP shear
        results[case]["Instability Ratio"] = {"Description": "Instability ratio", "SequenceComposantes": "Total"}
        # ratio = norm(AP, IS)/ML
        results[case]["Instability Ratio"]["Total"] = np.sqrt(
            (results[case]["Force_cisaillement"]["IS"])**2 + 
            (results[case]["Force_cisaillement"]["AP"])**2
        ) / abs(results[case]["Force_compression"]["ML"])
    
    print("Instability ratio calculated for all cases.")

# %% Create instability ratio comparison graphs
def create_instability_ratio_comparison(results, ref_case, compare_case, specific_angles=None):
    """
    Creates a comparison graph of the instability ratio between two cases
    
    Args:
        results: Loaded results
        ref_case: Reference case
        compare_case: Case to compare
        specific_angles: Specific angles for the table (default [10, 20, 40, 50, 60, 80, 100, 120])
    """
    if specific_angles is None:
        specific_angles = [10, 20, 40, 50, 60, 80, 100, 120]
    
    # Extract data for both cases
    ref_abduction = results[ref_case]['Abduction']['Total']
    ref_instability = results[ref_case]['Instability Ratio']['Total']
    
    comp_abduction = results[compare_case]['Abduction']['Total']
    comp_instability = results[compare_case]['Instability Ratio']['Total']
    
    # Create the figure for comparison
    plt.figure(figsize=(12, 6))
    
    # Plot the original curves
    plt.subplot(1, 2, 1)
    plt.plot(ref_abduction, ref_instability, label=f'{ref_case}', color='blue', linewidth=2)
    plt.plot(comp_abduction, comp_instability, label=f'{compare_case}', color='red', linewidth=2)
    plt.xlabel('Abduction angle (degrees)')
    plt.ylabel('Instability ratio')
    plt.title(f'Instability ratio: {ref_case} vs {compare_case}')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    # Calculate the percentage difference
    min_angle = max(min(ref_abduction), min(comp_abduction))
    max_angle = min(max(ref_abduction), max(comp_abduction))
    
    # Create a uniform angle grid for interpolation
    angles = np.linspace(min_angle, max_angle, 1000)
    
    # Interpolate instability values for both cases
    ref_interp = np.interp(angles, ref_abduction, ref_instability)
    comp_interp = np.interp(angles, comp_abduction, comp_instability)
    
    # Calculate the percentage difference
    diff_percent = ((comp_interp - ref_interp) / ref_interp) * 100
    
    # # Plot the difference (commented out in original)
    # plt.subplot(1, 2, 2)
    # plt.plot(angles, diff_percent, color='green', linewidth=2)
    # plt.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    # plt.xlabel('Abduction angle (degrees)')
    # plt.ylabel('Difference (%)')
    # plt.title(f'Percentage difference ({compare_case} - {ref_case})')
    # plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    # plt.savefig(f'instability_ratio_{ref_case}_vs_{compare_case}.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Interpolate values for specific angles
    ref_specific = np.interp(specific_angles, ref_abduction, ref_instability)
    comp_specific = np.interp(specific_angles, comp_abduction, comp_instability)
    
    # Calculate absolute difference
    diff_absolute = comp_specific - ref_specific
    
    # Create a DataFrame in the requested format
    data = {
        "Abduction angle": specific_angles,
        f"{compare_case}": np.round(comp_specific, 2),
        f"{ref_case}": np.round(ref_specific, 2),
        "Difference": np.round(diff_absolute, 2)
    }
    
    df_table = pd.DataFrame(data)
    
    # Display the formatted table
    print(f"\nTable of instability ratio values at specific angles ({ref_case} vs {compare_case}):")
    print(df_table.to_string(index=False))
    
    # Create a color-coded table
    create_colored_table(df_table, ref_case, compare_case)
    
    return df_table

# %% Create a colored table
def create_colored_table(df_table, ref_case, compare_case):
    """
    Creates a colored table for the instability ratio comparison
    
    Args:
        df_table: DataFrame containing the data
        ref_case: Reference case
        compare_case: Case to compare
    """
    # Create a DataFrame for display
    df_display = pd.DataFrame({
        "Abduction angle": [f"{angle}°" for angle in df_table["Abduction angle"]],
        f"{compare_case} ": [f"{val:.2f}" for val in df_table[f"{compare_case}"]],
        f"{ref_case} ": [f"{val:.2f}" for val in df_table[f"{ref_case}"]],
        "Difference ": [f"{val:.2f}" for val in df_table["Difference"]]
    })
    
    # Create the figure
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.axis('off')
    ax.axis('tight')
    
    # Create the table
    cell_text = df_display.values.tolist()
    table = ax.table(cellText=cell_text, colLabels=df_display.columns, cellLoc='center', loc='center')
    
    table.auto_set_column_width([0, 1, 2, 3])
    table.scale(2, 3)  # Increase table size
    
    # Header color
    header_color = '#CCCCCC'  # Light grey
    for i, key in enumerate(df_display.columns):
        cell = table[0, i]
        cell.set_text_props(weight='bold', color='black')
        cell.set_facecolor(header_color)
    
    # Apply a symmetric color scale around zero
    diff_values = df_table["Difference"].values
    max_diff = max(abs(diff_values))  # Maximum absolute value for normalization
    
    # Create a symmetric color palette (red-white-red)
    cmap_colors = ["red", "white", "red"]
    custom_cmap = mcolors.LinearSegmentedColormap.from_list("RedWhiteRed", cmap_colors)
    
    # Symmetric normalization between -max_diff and +max_diff
    norm = plt.Normalize(vmin=-max_diff, vmax=max_diff)
    
    # Color the cells in the Difference column
    for i in range(len(df_table)):
        diff_val = diff_values[i]
        color = custom_cmap(norm(diff_val))  # Apply normalized color
        cell = table[i + 1, 3]
        cell.set_facecolor(color)
        
        # Ensure text readability
        if abs(diff_val) > max_diff * 0.7:
            cell.set_text_props(color='white')
        else:
            cell.set_text_props(color='black')
    
    # Add a symmetric color bar around zero
    sm = plt.cm.ScalarMappable(cmap=custom_cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, orientation='horizontal', shrink=0.5, pad=0.1)
    cbar.set_label('Difference amplitude', fontsize=10)
    
    plt.title(f"Instability ratio comparison: {ref_case} vs {compare_case}", fontsize=14, pad=20)
    plt.figtext(0.5, 0.01, "Red: strong difference (positive or negative) | White: neutral", ha='center', fontsize=10)
    plt.tight_layout(rect=[0, 0.07, 1, 0.95])
    # plt.savefig(f'instability_table_{ref_case}_vs_{compare_case}.png', dpi=300, bbox_inches='tight')
    plt.show()

# %% Main function to analyze the instability ratio for all cases
def analyze_instability_ratio_all_cases(specific_angles=None):
    """
    Analyzes the instability ratio for all cases compared to the reference
    
    Args:
        specific_angles: Specific angles for the table (default [10, 20, 40, 50, 60, 80, 100, 120])
    """
    if specific_angles is None:
        specific_angles = [10, 20, 40,50, 60, 80, 100, 120]
    
    # Identify the reference and cases to compare
    ref_case, compare_cases = identify_reference_and_compare_cases(Results)
    
    if not ref_case:
        print("Cannot continue analysis without a reference case.")
        return
    
    if not compare_cases:
        print("No cases to compare with the reference.")
        return
    
    # Calculate the instability ratio for all cases
    calculate_instability_ratio(Results)
    
    # Global graph of the instability ratio for all cases
    from Anybody_Package.Anybody_Graph.GraphFunctions import graph
    graph(Results, "Abduction", "Instability Ratio", "Instability Ratio", cases_on="all", composante_y=["Total"])
    
    # Create a combined figure for all cases
    plt.figure(figsize=(14, 8))
    
    # Extract reference data
    ref_abduction = Results[ref_case]['Abduction']['Total']
    ref_instability = Results[ref_case]['Instability Ratio']['Total']
    
    # Plot the reference curve
    plt.plot(ref_abduction, ref_instability, label=f'{ref_case}', color='black', linewidth=2.5)
    
    # Colors for different cases
    colors = plt.cm.tab10(np.linspace(0, 1, len(compare_cases)))
    
    # Plot all comparison curves
    for i, comp_case in enumerate(compare_cases):
        comp_abduction = Results[comp_case]['Abduction']['Total']
        comp_instability = Results[comp_case]['Instability Ratio']['Total']
        plt.plot(comp_abduction, comp_instability, label=f'{comp_case}', color=colors[i], linewidth=2)
    
    plt.xlabel('Abduction angle (degrees)')
    plt.ylabel('Instability ratio')
    plt.title(f'Instability ratio: {ref_case} vs all cases')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(loc='best')
    plt.tight_layout()
    # plt.savefig('instability_ratio_all_cases.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # For each case to compare, create a comparison graph
    all_tables = []
    for comp_case in compare_cases:
        print(f"\nInstability ratio analysis: {ref_case} vs {comp_case}")
        df_table = create_instability_ratio_comparison(Results, ref_case, comp_case, specific_angles)
        all_tables.append(df_table)
    
    # Create a global table of all comparisons
    if all_tables:
        # Create the combined DataFrame
        df_combined = pd.DataFrame({"Abduction angle": specific_angles})
        
        # Add reference values
        ref_specific = np.interp(specific_angles, Results[ref_case]['Abduction']['Total'], 
                                Results[ref_case]['Instability Ratio']['Total'])
        df_combined[ref_case] = np.round(ref_specific, 2)
        
        # Add each case with its difference
        for i, comp_case in enumerate(compare_cases):
            comp_specific = np.interp(specific_angles, Results[comp_case]['Abduction']['Total'], 
                                    Results[comp_case]['Instability Ratio']['Total'])
            df_combined[comp_case] = np.round(comp_specific, 2)
            diff_col = f"Diff_{comp_case}"
            df_combined[diff_col] = np.round(comp_specific - ref_specific, 2)
            
        # Save the global table
        # df_combined.to_csv('instability_ratio_comparison.csv', index=False)
        # print("\nGlobal table of all comparisons:")
        # print(df_combined.to_string(index=False))
        
    print("\nInstability ratio analysis completed.")

# %% Main execution
if __name__ == "__main__":
    analyze_instability_ratio_all_cases()