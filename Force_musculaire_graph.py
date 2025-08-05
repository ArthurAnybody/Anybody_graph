import os
os.chdir(r"C:\Users\Documents\Python")# chemin a modfier
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
from type_colors import FIXED_TYPE_COLORS

# Variable to store the path to a file with selected results
SELECTED_RESULTS_FILE = None

# %% List of muscle categories
Muscles_Main = [
    "Deltoideus anterior",
    "Deltoideus lateral",
    "Deltoideus posterior",
    "Infraspinatus",
    "Supraspinatus",
     # "Subscapularis",
    "Upper subscapularis", 
    "Lower subscapularis",
    "Teres minor",
    # "Lower trapezius",
    # "Middle trapezius",
    # "Upper trapezius",
    "Trapezius",
    
    # "Biceps brachii long head",  ## Activer ou désactiver ce muscle pour affiche le graphique differences % entre ref et le type
    # "Biceps brachii short head", 
    "Biceps brachii", ## le biceps brachii sera Inactif si vous laisser ce muscle dans le le graphique differences % entre ref et le type
]
 
Muscles_Aux = [
    "Pectoralis major clavicular",
    "Pectoralis major sternal",
    "Pectoralis minor",
    "Teres major",
    "Teres minor",
    "Rhomboideus",
    "Serratus anterior",
    # "Biceps brachii long head",
    # "Biceps brachii short head"
]

Muscles_Extra = [
    "Sternocleidomastoid sternum",
    "Sternocleidomastoid clavicular",
    "Latissimus dorsi",
    "Levator scapulae",
    "Coracobrachialis",
    "Triceps long head",
]

def get_type_colors(type_cases):
    type_colors = {}
    for type_key, case_name in type_cases.items():
        if case_name in FIXED_TYPE_COLORS:
            type_colors[type_key] = FIXED_TYPE_COLORS[case_name]
        elif type_key == 'Reference':
            type_colors[type_key] = FIXED_TYPE_COLORS['Reference']
        else:
            type_colors[type_key] = '#cccccc'  # couleur par défaut
    return type_colors

def reorder_cases(cases):
    """
    Trie les cas avec 'Reference' en premier, suivi de Type A à E
    """
    order = ["Reference", "Type A", "Type B", "Type C", "Type D", "Type E"]
    return sorted(cases, key=lambda c: order.index(c) if c in order else 999)


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
    SaveSimulationsDirectory = "C:/Users/Documents/Python/Saved Simulations")# chemin a modfier
    
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
SaveSimulationsDirectory = "C:/Users/Documents/Python/Saved Simulations")# chemin a modfier
Results = load_results_from_file(SaveSimulationsDirectory, "Results")

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
    
    # Create a version for textual display of percentages with force differences
    df_display = pd.DataFrame(index=df_diff.index, columns=df_diff.columns, dtype=object)
    df_display = df_display.fillna("")
    
    # Keep track of completely inactive muscles
    inactive_muscles = set()
    
    # Format percentages for display and add force differences
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
            
            # Calculate force difference
            force_diff = comp_val - ref_val
            
            # Format based on status
            if status == "muscle_inactive":
                df_display.loc[muscle, col] = "Inactive"
            elif status == "zero":
                # Just display 0% for zero values with force difference
                df_display.loc[muscle, col] = f"0.0%\n({force_diff:+.0f}N)"
            elif status == "normal":
                # For very high values, cap the displayed percentage
                if diff_val > 999:
                    df_display.loc[muscle, col] = f">999%\n({force_diff:+.0f}N)"
                else:
                    df_display.loc[muscle, col] = f"{diff_val:.0f}%\n({force_diff:+.0f}N)"
            else:
                # Fallback for unexpected status
                df_display.loc[muscle, col] = f"??\n({force_diff:+.0f}N)"
    
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
                    color='darkgrey',
                    alpha=0.8,           # Opacity
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
    

# %% Control the font size for graphs
matplotlib.rcParams.update({'font.size': 12})
matplotlib.rcParams.update({'axes.titlesize': 14})
matplotlib.rcParams.update({'figure.titlesize': 16})
matplotlib.rcParams.update({'axes.labelsize': 12})
matplotlib.rcParams.update({'xtick.labelsize': 10})
matplotlib.rcParams.update({'ytick.labelsize': 10})
matplotlib.rcParams.update({'legend.fontsize': 10})

# %% Data extraction for all cases
def extract_all_cases_data(results, muscles, angle_ranges):
    all_cases_data = {}
    available_cases = list(results.keys())

    for case_name in available_cases:
        case_data = {}

        try:
            abduction_angles = results[case_name]['Abduction']['Total']
        except KeyError:
            abduction_angles = []

        for muscle in muscles:
            case_data[muscle] = []

            if muscle == "Biceps brachii":
                try:
                    long = results[case_name]["Muscles"]["Biceps brachii long head"]["Biceps brachii long head"]["Ft"]["Total"]
                    short = results[case_name]["Muscles"]["Biceps brachii short head"]["Biceps brachii short head"]["Ft"]["Total"]
                    if len(long) != len(abduction_angles) or len(short) != len(abduction_angles):
                        case_data[muscle] = [0.0] * len(angle_ranges)
                        continue
                    combined = [l + s for l, s in zip(long, short)]
                    for start, end in angle_ranges:
                        indices = [i for i, a in enumerate(abduction_angles) if start <= a <= end]
                        val = np.mean([combined[i] for i in indices]) if indices else 0.0
                        case_data[muscle].append(val)
                except KeyError:
                    case_data[muscle] = [0.0] * len(angle_ranges)
            else:
                try:
                    force_data = results[case_name]["Muscles"][muscle][muscle]["Ft"]["Total"]
                    if len(force_data) != len(abduction_angles):
                        case_data[muscle] = [0.0] * len(angle_ranges)
                        continue
                    for start, end in angle_ranges:
                        indices = [i for i, a in enumerate(abduction_angles) if start <= a <= end]
                        val = np.mean([force_data[i] for i in indices]) if indices else 0.0
                        case_data[muscle].append(val)
                except KeyError:
                    case_data[muscle] = [0.0] * len(angle_ranges)

        all_cases_data[case_name] = case_data

    return all_cases_data


def create_horizontal_bar_chart(all_cases_data, muscles, angle_ranges, case_colors):
    import matplotlib.pyplot as plt
    import matplotlib

    # Set consistent font family and size globally
    matplotlib.rcParams.update({
        
        'font.size': 14,
        'axes.titlesize': 16,
        'axes.labelsize': 14,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'legend.fontsize': 12
    })

    cases = reorder_cases(list(all_cases_data.keys()))

    for idx, (start, end) in enumerate(angle_ranges):
        # Wider and taller figure
        fig, ax = plt.subplots(figsize=(14, max(10, len(muscles) * 0.8)))  
        y_pos = np.arange(len(muscles))
        width = 0.8 / len(cases)

        for i, case in enumerate(cases):
            forces = [all_cases_data[case][muscle][idx] for muscle in muscles]
            y_offset = y_pos + (i - len(cases)/2 + 0.5) * width
            color = case_colors.get(case, '#cccccc')

            bars = ax.barh(y_offset, forces, width, label=case,
                           color=color, alpha=0.8, edgecolor='black')

            # Add value annotations
            for bar, val in zip(bars, forces):
                if val > 0.1:
                    ax.text(bar.get_width() + 3, bar.get_y() + bar.get_height()/2.0,
                            f'{round(val)}', va='center', ha='left', fontsize=12)

        ax.set_title(f'Muscle Forces – Angles {start}° to {end}°', fontweight='bold', pad=15)
        ax.set_xlabel("Force (N)")
        ax.set_ylabel("Muscles")
        ax.set_yticks(y_pos)
        ax.set_yticklabels(muscles, fontsize=13)
        ax.invert_yaxis()
        ax.grid(True, axis='x', alpha=0.3)
        ax.set_xlim(left=0)

        # Adjust legend outside plot
        ax.legend(title="Cases", title_fontsize=13, bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0.)
        
        plt.tight_layout()
        plt.show()



def create_summary_bar_chart(all_cases_data, muscles, angle_ranges, case_colors):
    cases = reorder_cases(list(all_cases_data.keys()))
    case_totals = {case: sum(all_cases_data[case][m][i]
                     for m in muscles for i in range(len(angle_ranges))) for case in cases}

    muscle_means = {
        m: np.mean([all_cases_data[c][m][i]
        for c in cases for i in range(len(angle_ranges))]) for m in muscles
    }

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # Total par cas
    colors = [case_colors.get(c, '#ccc') for c in cases]
    bars1 = ax1.bar(cases, [case_totals[c] for c in cases], color=colors,
                    edgecolor='black', linewidth=1)
    for bar, val in zip(bars1, [case_totals[c] for c in cases]):
        ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01,
                 f'{round(val)}', ha='center', va='bottom', fontsize=10)
    ax1.set_title("Force Totale par Cas", fontsize=14, fontweight='bold')
    ax1.set_xlabel("Cas")
    ax1.set_ylabel("Force (N)")
    ax1.grid(True, axis='y', alpha=0.3)
    ax1.set_xticklabels(cases, rotation=45, ha='right')

    # Top 8 muscles
    top = sorted(muscle_means.items(), key=lambda x: x[1], reverse=True)[:8]
    names = [m[:15] + '...' if len(m) > 15 else m for m, _ in top]
    values = [v for _, v in top]
    bars2 = ax2.barh(names, values, color=plt.cm.Set3(np.linspace(0, 1, 8)),
                     edgecolor='black', linewidth=1)
    for bar, val in zip(bars2, values):
        ax2.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2.,
                 f'{round(val, 1)}', va='center', fontsize=10)
    ax2.set_title("Top 8 Muscles (Force Moyenne)", fontsize=14, fontweight='bold')
    ax2.set_xlabel("Force Moyenne (N)")
    ax2.set_ylabel("Muscles")
    ax2.grid(True, axis='x', alpha=0.3)

    plt.tight_layout()
    plt.show()

def generate_bar_chart_analysis(muscles_to_analyze=None):
    if muscles_to_analyze is None:
        muscles_to_analyze = Muscles_Main

    angle_ranges = [(10, 30), (30, 60), (60, 90), (90, 120)]
    all_cases_data = extract_all_cases_data(Results, muscles_to_analyze, angle_ranges)
    if not all_cases_data:
        print("Aucune donnée disponible.")
        return

    type_cases = {case: case for case in all_cases_data.keys()}
    case_colors = get_type_colors(type_cases)

    create_horizontal_bar_chart(all_cases_data, muscles_to_analyze, angle_ranges, case_colors)
    # create_summary_bar_chart(all_cases_data, muscles_to_analyze, angle_ranges, case_colors)


# %% Exécution
if __name__ == "__main__":
    # Générer l'analyse complète avec les muscles principaux
    generate_bar_chart_analysis(Muscles_Main)
    
    # Optionnel: analyser d'autres groupes
    # generate_bar_chart_analysis(Muscles_Aux)
    # generate_bar_chart_analysis(Muscles_Extra)
    
    # Si vous préférez analyser les muscles par catégorie, décommentez les lignes suivantes
    generate_all_difference_graphs(Muscles_Main)
    # generate_all_difference_graphs(Muscles_Aux)
    # generate_all_difference_graphs(Muscles_Extra)




