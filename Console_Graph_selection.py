Test console, doesn t work

import os
import sys
import importlib.util
import traceback
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, StringVar
import threading
import io
import webbrowser
from contextlib import redirect_stdout, redirect_stderr
import matplotlib
matplotlib.use("TkAgg")  # Utiliser le backend TkAgg pour intégrer dans Tkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib import cm, colors
import datetime
import pickle


class ConsoleRedirector:
    def __init__(self):
        self.buffer = []
    
    def write(self, string):
        self.buffer.append(string)
    
    def flush(self):
        pass
    
    def get_output(self):
        return ''.join(self.buffer)


class SimulationSelector:
    """Classe pour gérer la sélection des simulations à analyser"""
    
    def __init__(self, parent_window, simulation_directory, callback):
        """
        Initialise le sélecteur de simulations
        
        Parameters:
        -----------
        parent_window : tk.Tk ou tk.Toplevel
            Fenêtre parente
        simulation_directory : str
            Chemin vers le répertoire contenant les simulations sauvegardées
        callback : function
            Fonction à appeler lorsque les simulations sont sélectionnées
        """
        self.parent = parent_window
        self.sim_directory = simulation_directory
        self.callback = callback
        
        # Créer une fenêtre de sélection
        self.window = tk.Toplevel(self.parent)
        self.window.title("Sélection des Simulations")
        self.window.geometry("650x500")
        self.window.transient(self.parent)  # Fenêtre toujours au-dessus de la fenêtre parente
        
        # Charger les résultats disponibles
        self.available_results = self.load_available_results()
        
        # Créer l'interface
        self.create_interface()
    
    def load_available_results(self):
        """Charge les résultats disponibles à partir des fichiers .pkl"""
        results = {}
        
        try:
            # Chercher le fichier Results.pkl
            results_file = os.path.join(self.sim_directory, "Results.pkl")
            if os.path.exists(results_file):
                with open(results_file, 'rb') as f:
                    results = pickle.load(f)
            else:
                # Si le fichier principal n'existe pas, chercher des fichiers .pkl individuels
                for file in os.listdir(self.sim_directory):
                    if file.endswith(".pkl"):
                        try:
                            with open(os.path.join(self.sim_directory, file), 'rb') as f:
                                data = pickle.load(f)
                                # Si c'est un dictionnaire de résultats, fusionner
                                if isinstance(data, dict) and "simulations" in data:
                                    results.setdefault("simulations", {})[sim_name] = sim_data
                        except Exception as e:
                            print(f"Erreur lors du chargement du fichier {file}: {e}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des résultats: {e}")
            return {"simulations": {}}
        
        return results
    
    def create_interface(self):
        """Crée l'interface de sélection des simulations"""
        # Frame principal
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Label d'instructions
        instructions = ttk.Label(main_frame, 
                                text="Sélectionnez les simulations à inclure dans l'analyse:", 
                                font=("Arial", 12, "bold"))
        instructions.pack(pady=(0, 10), anchor=tk.W)
        
        # Frame pour la liste de simulations avec scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Liste des simulations
        self.simulation_listbox = tk.Listbox(list_frame, 
                                            selectmode=tk.MULTIPLE,
                                            font=("Arial", 11),
                                            yscrollcommand=scrollbar.set)
        self.simulation_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.simulation_listbox.yview)
        
        # Remplir la liste avec les simulations disponibles
        if "simulations" in self.available_results:
            for sim_name in sorted(self.available_results["simulations"].keys()):
                self.simulation_listbox.insert(tk.END, sim_name)
        
        # Frame pour les boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Bouton pour sélectionner tout
        select_all_button = ttk.Button(button_frame, 
                                       text="Sélectionner tout", 
                                       command=self.select_all)
        select_all_button.pack(side=tk.LEFT, padx=5)
        
        # Bouton pour désélectionner tout
        deselect_all_button = ttk.Button(button_frame, 
                                         text="Désélectionner tout", 
                                         command=self.deselect_all)
        deselect_all_button.pack(side=tk.LEFT, padx=5)
        
        # Bouton pour filtrer par nom
        filter_button = ttk.Button(button_frame, 
                                   text="Filtrer", 
                                   command=self.show_filter_dialog)
        filter_button.pack(side=tk.LEFT, padx=5)
        
        # Frame pour la zone de recherche
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=5)
        
        # Label de recherche
        search_label = ttk.Label(search_frame, text="Rechercher:")
        search_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Entrée de recherche
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.search_simulations)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Frame pour les boutons d'action
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        # Bouton Valider
        validate_button = ttk.Button(action_frame, 
                                    text="Valider la sélection", 
                                    command=self.validate_selection,
                                    style="Accent.TButton")
        validate_button.pack(side=tk.RIGHT, padx=5)
        
        # Bouton Annuler
        cancel_button = ttk.Button(action_frame, 
                                  text="Annuler", 
                                  command=self.cancel)
        cancel_button.pack(side=tk.RIGHT, padx=5)
        
        # Style pour le bouton Valider
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Arial", 11, "bold"))
        
        # Centrer la fenêtre par rapport à la fenêtre parente
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() - width) // 2
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() - height) // 2
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Rendre la fenêtre modale (bloquer l'interaction avec la fenêtre parente)
        self.window.grab_set()
    
    def select_all(self):
        """Sélectionne toutes les simulations dans la liste"""
        self.simulation_listbox.selection_set(0, tk.END)
    
    def deselect_all(self):
        """Désélectionne toutes les simulations dans la liste"""
        self.simulation_listbox.selection_clear(0, tk.END)
    
    def search_simulations(self, *args):
        """Filtre les simulations en fonction du texte de recherche"""
        search_text = self.search_var.get().lower()
        
        # Effacer la liste
        self.simulation_listbox.delete(0, tk.END)
        
        # Remplir avec les simulations correspondantes
        if "simulations" in self.available_results:
            for sim_name in sorted(self.available_results["simulations"].keys()):
                if search_text in sim_name.lower():
                    self.simulation_listbox.insert(tk.END, sim_name)
    
    def show_filter_dialog(self):
        """Affiche une boîte de dialogue pour filtrer les simulations par préfixe"""
        filter_window = tk.Toplevel(self.window)
        filter_window.title("Filtrer par préfixe")
        filter_window.geometry("300x150")
        filter_window.transient(self.window)
        filter_window.grab_set()
        
        # Frame principal
        frame = ttk.Frame(filter_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Label d'instructions
        instructions = ttk.Label(frame, text="Entrez un préfixe pour filtrer les simulations:")
        instructions.pack(pady=(0, 10))
        
        # Entrée de préfixe
        prefix_var = tk.StringVar()
        prefix_entry = ttk.Entry(frame, textvariable=prefix_var, width=30)
        prefix_entry.pack(pady=5)
        prefix_entry.focus_set()
        
        # Boutons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Bouton Filtrer
        def apply_filter():
            prefix = prefix_var.get()
            if prefix:
                # Effacer la liste
                self.simulation_listbox.delete(0, tk.END)
                
                # Remplir avec les simulations correspondantes
                if "simulations" in self.available_results:
                    for sim_name in sorted(self.available_results["simulations"].keys()):
                        if sim_name.startswith(prefix):
                            self.simulation_listbox.insert(tk.END, sim_name)
            
            filter_window.destroy()
        
        filter_button = ttk.Button(button_frame, text="Filtrer", command=apply_filter)
        filter_button.pack(side=tk.RIGHT, padx=5)
        
        # Bouton Annuler
        cancel_button = ttk.Button(button_frame, text="Annuler", command=filter_window.destroy)
        cancel_button.pack(side=tk.RIGHT, padx=5)
        
        # Centrer la fenêtre
        filter_window.update_idletasks()
        width = filter_window.winfo_width()
        height = filter_window.winfo_height()
        x = self.window.winfo_rootx() + (self.window.winfo_width() - width) // 2
        y = self.window.winfo_rooty() + (self.window.winfo_height() - height) // 2
        filter_window.geometry(f"{width}x{height}+{x}+{y}")
    
    def validate_selection(self):
        """Valide la sélection des simulations et retourne les résultats"""
        # Récupérer les indices des simulations sélectionnées
        selected_indices = self.simulation_listbox.curselection()
        
        if not selected_indices:
            messagebox.showwarning("Avertissement", "Aucune simulation sélectionnée")
            return
        
        # Récupérer les noms des simulations sélectionnées
        selected_simulations = [self.simulation_listbox.get(i) for i in selected_indices]
        
        # Créer un sous-ensemble des résultats avec les simulations sélectionnées
        selected_results = {"simulations": {}}
        for sim_name in selected_simulations:
            if sim_name in self.available_results["simulations"]:
                selected_results["simulations"][sim_name] = self.available_results["simulations"][sim_name]
        
        # Copier les autres clés du dictionnaire original
        for key in self.available_results:
            if key != "simulations":
                selected_results[key] = self.available_results[key]
        
        # Appeler le callback avec les résultats sélectionnés
        self.callback(selected_results)
        
        # Fermer la fenêtre
        self.window.destroy()
    
    def cancel(self):
        """Annule la sélection et ferme la fenêtre"""
        self.callback(None)  # Appeler le callback avec None pour indiquer l'annulation
        self.window.destroy()


class AnalysisLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Lanceur d'Analyses AnyBody")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Pour stocker les figures matplotlib
        self.figures = []
        # Pour suivre le prochain ID de figure
        self.next_figure_id = 1
        
        # Paramètres de visualisation par défaut
        self.default_cmap = "viridis"
        self.default_style = "seaborn-v0_8"
        self.available_cmaps = ["viridis", "plasma", "inferno", "magma", "cividis", 
                               "Greys", "Blues", "Reds", "YlOrBr", "RdBu", "jet"]
        self.available_styles = plt.style.available
        
        # Thème actuel
        self.current_theme = "light"
        
        # Configuration des styles
        self.style = ttk.Style()
        self.apply_theme(self.current_theme)
        
        # Créer la barre de menu principale
        self.create_menu()
        
        # Créer le notebook principal (conteneur d'onglets)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Créer le premier onglet pour le menu principal
        self.main_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.main_tab, text="Menu Principal")
        
        # Associer les raccourcis clavier
        self.setup_keyboard_shortcuts()
        
        # En-tête du menu principal
        header_frame = ttk.Frame(self.main_tab)
        header_frame.pack(fill='x', pady=20)
        
        title_label = ttk.Label(header_frame, text="Analyse biomécanique de l'épaule", style="Title.TLabel")
        title_label.pack()
        
        subtitle_label = ttk.Label(header_frame, text="Sélectionnez l'analyse de résultats à exécuter", style="Subtitle.TLabel")
        subtitle_label.pack(pady=5)
        
        # Boutons pour les différentes analyses
        button_frame = ttk.Frame(self.main_tab)
        button_frame.pack(fill='both', expand=True, padx=50, pady=20)
        
        # Options pour les boutons
        button_style = {"width": 30, "padding": 10}
        
        # Bouton 1: Analyse de l'activité musculaire
        self.btn_activite = ttk.Button(
            button_frame, 
            text="1. Analyse de la force musculaire",
            command=lambda: self.run_analysis_with_selection("Force Musculaire", self.lancer_activite_musculaire),
            **button_style
        )
        self.btn_activite.pack(pady=10)
        
        # Bouton 2: Translations APIs
        self.btn_translations = ttk.Button(
            button_frame, 
            text="2. Translations AP-IS",
            command=lambda: self.run_analysis_with_selection("Translations AP-IS", self.lancer_translations_apis),
            **button_style
        )
        self.btn_translations.pack(pady=10)
        
        # Bouton 3: Ratio d'instabilité
        self.btn_ratio = ttk.Button(
            button_frame, 
            text="3. Ratio d'instabilité",
            command=lambda: self.run_analysis_with_selection("Ratio d'Instabilité", self.lancer_ratio_instabilite),
            **button_style
        )
        self.btn_ratio.pack(pady=10)
        
        # Bouton 4: Analyse des résultats
        self.btn_analyse = ttk.Button(
            button_frame, 
            text="4. Analyse globale des résultats",
            command=lambda: self.run_analysis_with_selection("Analyse des Résultats", self.lancer_analyse_resultats),
            **button_style
        )
        self.btn_analyse.pack(pady=10)
        
        # Bouton Quitter
        self.btn_quitter = ttk.Button(
            button_frame, 
            text="Quitter",
            command=self.root.destroy,
            **button_style
        )
        self.btn_quitter.pack(pady=25)
        
        # Pied de page
        footer_frame = ttk.Frame(self.main_tab)
        footer_frame.pack(fill='x', pady=20)
        
        footer_label = ttk.Label(footer_frame, text="© 2025 - LIO Biomécanique - Analyse des données d'AnyBody", style="Footer.TLabel")
        footer_label.pack()
        
        # Configuration du répertoire de travail
        try:
            os.chdir(r"C:\Users\p0137717\Documents\Python")
        except Exception as e:
            print(f"Erreur lors du changement de répertoire: {e}")
            
        # Ajout des méthodes nécessaires pour l'importation de modules
        self.modules_cache = {}
        
        # Redéfinir la fonction show de matplotlib pour capturer les figures
        self.original_plt_show = plt.show
        plt.show = self.custom_plt_show
        
        # Créer un dictionnaire pour stocker les analyses et leurs figures
        self.analysis_figures = {}
        
        # Répertoire par défaut pour les sauvegardes
        self.default_save_dir = os.path.join(os.path.expanduser("~"), "Documents", "AnyBody_Resultats")
        # Créer le répertoire s'il n'existe pas
        if not os.path.exists(self.default_save_dir):
            try:
                os.makedirs(self.default_save_dir)
            except Exception as e:
                print(f"Erreur lors de la création du répertoire de sauvegarde: {e}")
                self.default_save_dir = os.path.expanduser("~")
        
        # Répertoire contenant les simulations
        self.simulations_directory = "C:/Users/p0137717/Documents/Python/Saved Simulations"
        
        # Variable pour stocker les résultats sélectionnés
        self.selected_results = None

    def apply_theme(self, theme_name):
        """Applique un thème à l'interface"""
        self.current_theme = theme_name
        
        if theme_name == "light":
            # Thème clair
            bg_color = "#F0F0F0"
            fg_color = "#000000"
            self.style.configure("TFrame", background=bg_color)
            self.style.configure("TButton", font=("Arial", 11), background=bg_color)
            self.style.configure("Title.TLabel", font=("Arial", 18, "bold"), background=bg_color, foreground=fg_color)
            self.style.configure("Subtitle.TLabel", font=("Arial", 12), background=bg_color, foreground=fg_color)
            self.style.configure("Footer.TLabel", font=("Arial", 8), background=bg_color, foreground=fg_color)
            self.root.configure(background=bg_color)
            
            # Changer le style matplotlib pour un fond clair
            plt.style.use('default')
            
        elif theme_name == "dark":
            # Thème sombre
            bg_color = "#2E2E2E"
            fg_color = "#FFFFFF"
            self.style.configure("TFrame", background=bg_color)
            self.style.configure("TButton", font=("Arial", 11), background=bg_color)
            self.style.configure("Title.TLabel", font=("Arial", 18, "bold"), background=bg_color, foreground=fg_color)
            self.style.configure("Subtitle.TLabel", font=("Arial", 12), background=bg_color, foreground=fg_color)
            self.style.configure("Footer.TLabel", font=("Arial", 8), background=bg_color, foreground=fg_color)
            self.root.configure(background=bg_color)
            
            # Changer le style matplotlib pour un fond sombre
            plt.style.use('dark_background')

    def run_analysis_with_selection(self, title, analysis_func):
        """Lance l'analyse après avoir sélectionné les simulations"""
        # Ouvrir le sélecteur de simulations
        SimulationSelector(self.root, self.simulations_directory, 
                            lambda results: self.handle_simulation_selection(title, analysis_func, results))
    
    def handle_simulation_selection(self, title, analysis_func, selected_results):
        """Gère le retour du sélecteur de simulations"""
        if selected_results is None:
            # L'utilisateur a annulé la sélection
            return
        
        # Stocker les résultats sélectionnés
        self.selected_results = selected_results
        
        # Lancer l'analyse avec les résultats sélectionnés
        self.run_analysis(title, analysis_func)
    
    def custom_plt_show(self, *args, **kwargs):
        """
        Remplace la fonction plt.show standard pour capturer les figures
        et les afficher dans l'interface Tkinter
        """
        # Capture la figure actuelle
        fig = plt.gcf()
        
        # Ajouter la figure à la liste
        self.figures.append(fig)
        
        # Identifier dans quelle analyse nous sommes
        if hasattr(self, 'current_analysis'):
            if self.current_analysis not in self.analysis_figures:
                self.analysis_figures[self.current_analysis] = []
            
            # Stocker la figure pour cette analyse
            fig_id = self.next_figure_id
            self.next_figure_id += 1
            self.analysis_figures[self.current_analysis].append((fig_id, fig))
            
            # Créer un nouvel onglet pour cette figure s'il y a déjà un notebook d'analyse
            if hasattr(self, 'analysis_notebook') and self.analysis_notebook:
                # Créer un titre pour l'onglet
                tab_title = f"Fig {fig_id}"
                
                # Créer un nouvel onglet et y afficher la figure
                self.add_figure_tab(fig, tab_title)
        
        # On n'affiche pas la figure dans une fenêtre pop-up
        plt.close(fig)  # Fermer la figure pour éviter la fenêtre popup

    def add_figure_tab(self, fig, tab_title):
        """
        Ajoute un nouvel onglet dans le notebook d'analyse et y affiche la figure
        """
        # Créer l'onglet
        fig_tab = ttk.Frame(self.analysis_notebook)
        self.analysis_notebook.add(fig_tab, text=tab_title)
        
        # Afficher la figure dans l'onglet
        canvas = FigureCanvasTkAgg(fig, master=fig_tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Ajouter une barre d'outils de navigation (zoom, pan, etc.)
        toolbar_frame = ttk.Frame(fig_tab)
        toolbar_frame.pack(fill='x')
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()
        
        # Ajouter un bouton de sauvegarde spécifique
        save_button = ttk.Button(
            toolbar_frame,
            text="Enregistrer cette figure",
            command=lambda f=fig, t=tab_title: self.save_figure(f, t)
        )
        save_button.pack(side=tk.RIGHT, padx=5)
        
        # Ajouter un bouton de personnalisation
        customize_button = ttk.Button(
            toolbar_frame,
            text="Personnaliser",
            command=lambda f=fig, t=tab_title: self.customize_figure(f, t)
        )
        customize_button.pack(side=tk.RIGHT, padx=5)
        
        # Mettre à jour le canvas
        canvas.draw_idle()
        
        # Sélectionner ce nouvel onglet
        self.analysis_notebook.select(fig_tab)

    def run_analysis(self, title, analysis_func):
        """
        Crée un onglet pour l'analyse et exécute l'analyse
        """
        # Mettre à jour l'analyse courante
        self.current_analysis = title
        
        # Créer un nouvel onglet pour l'analyse dans le notebook principal
        analysis_tab = ttk.Frame(self.notebook)
        self.notebook.add(analysis_tab, text=title)
        self.notebook.select(analysis_tab)
        
        # Créer un nouveau notebook pour les figures
        self.analysis_notebook = ttk.Notebook(analysis_tab)
        self.analysis_notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Ajouter un onglet d'attente
        waiting_tab = ttk.Frame(self.analysis_notebook)
        self.analysis_notebook.add(waiting_tab, text="En cours...")
        
        # Message d'attente
        ttk.Label(waiting_tab, text="Analyse en cours, veuillez patienter...", style="Subtitle.TLabel").pack(pady=20)
        
        # Indicateur de progrès
        progress = ttk.Progressbar(waiting_tab, mode='indeterminate')
        progress.pack(fill='x', padx=50, pady=10)
        progress.start()
        
        # Boutons de contrôle
        control_frame = ttk.Frame(analysis_tab)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        # Bouton pour sauvegarder toutes les figures
        btn_save_all = ttk.Button(
            control_frame,
            text="Enregistrer toutes les figures",
            command=self.save_all_figures
        )
        btn_save_all.pack(side=tk.LEFT, padx=5)
        
        # Bouton de comparaison de figures
        btn_compare = ttk.Button(
            control_frame,
            text="Comparer les figures",
            command=self.compare_figures
        )
        btn_compare.pack(side=tk.LEFT, padx=5)
        
        # Bouton pour changer les simulations sélectionnées
        btn_change_selection = ttk.Button(
            control_frame,
            text="Changer la sélection",
            command=lambda: self.run_analysis_with_selection(title, analysis_func)
        )
        btn_change_selection.pack(side=tk.LEFT, padx=5)
        
        # Bouton pour voir les simulations sélectionnées
        btn_view_selection = ttk.Button(
            control_frame,
            text="Voir la sélection actuelle",
            command=self.show_current_selection
        )
        btn_view_selection.pack(side=tk.LEFT, padx=5)
        
        btn_close = ttk.Button(
            control_frame, 
            text="Fermer cette analyse",
            command=lambda: self.close_tab(analysis_tab)
        )
        btn_close.pack(side=tk.RIGHT, padx=5)
        
        # Rediriger la sortie standard et stderr
        stdout_redirector = ConsoleRedirector()
        stderr_redirector = ConsoleRedirector()
        
        # Lancer l'analyse dans un thread séparé
        def run_analysis_thread():
            with redirect_stdout(stdout_redirector), redirect_stderr(stderr_redirector):
                try:
                    # Exécuter l'analyse avec les résultats sélectionnés
                    if self.selected_results:
                        # Sauvegarder temporairement les résultats sélectionnés dans un fichier
                        temp_file = os.path.join(self.simulations_directory, "temp_selection.pkl")
                        with open(temp_file, 'wb') as f:
                            pickle.dump(self.selected_results, f)
                        
                        # Charger temporairement ce fichier dans le module
                        analysis_func(temp_file)
                        
                        # Supprimer le fichier temporaire
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                    else:
                        # Si aucune sélection n'a été faite, utiliser l'analyse par défaut
                        analysis_func()
                except Exception as e:
                    print(f"Erreur lors de l'exécution de l'analyse: {e}")
                    print(traceback.format_exc())
            
            # Une fois l'analyse terminée, supprimer l'onglet d'attente si des figures ont été créées
            self.root.after(100, lambda: self.finish_analysis(waiting_tab))
        
        analysis_thread = threading.Thread(target=run_analysis_thread)
        analysis_thread.daemon = True
        analysis_thread.start()

    def finish_analysis(self, waiting_tab):
        """
        Finalise l'analyse après son exécution
        """
        # Vérifier si des onglets de figure ont été ajoutés (autres que l'onglet d'attente)
        if self.analysis_notebook.index('end') > 1:
            # D'autres onglets de figure ont été ajoutés, supprimer l'onglet d'attente
            self.analysis_notebook.forget(waiting_tab)
            
            # Sélectionner le premier onglet de figure
            self.analysis_notebook.select(0)
        else:
            # Aucune figure n'a été générée, mettre à jour l'onglet d'attente
            for widget in waiting_tab.winfo_children():
                widget.destroy()
            
            ttk.Label(waiting_tab, text="Aucun graphique généré", style="Subtitle.TLabel").pack(pady=20)
            
            # Ajouter un bouton pour réessayer avec une autre sélection
            retry_button = ttk.Button(
                waiting_tab,
                text="Changer la sélection de simulations",
                command=lambda: self.run_analysis_with_selection(self.current_analysis, 
                                                              self.get_analysis_function(self.current_analysis))
            )
            retry_button.pack(pady=10)

    def close_tab(self, tab):
        """Ferme l'onglet spécifié"""
        self.notebook.forget(self.notebook.index(tab))
        # Retourner au menu principal
        self.notebook.select(0)
    
    def importer_module(self, nom_fichier):
        """
        Importe dynamiquement un module Python par son nom de fichier
        """
        try:
            # Vérifier si le module est déjà en cache
            if nom_fichier in self.modules_cache:
                return self.modules_cache[nom_fichier]
                
            # Vérifier si le fichier existe
            chemin_complet = os.path.join(r"C:\Users\p0137717\Documents\Python", f"{nom_fichier}.py")
            if not os.path.exists(chemin_complet):
                print(f"Erreur: Le fichier {chemin_complet} n'existe pas.")
                return None
            
            # Charger le module
            spec = importlib.util.spec_from_file_location(nom_fichier, chemin_complet)
            if spec is None:
                print(f"Erreur: Impossible de charger le module depuis {chemin_complet}")
                return None
                
            module = importlib.util.module_from_spec(spec)
            
            # Ajouter une variable pour le fichier de sélection
            module.SELECTED_RESULTS_FILE = None
            
            sys.modules[nom_fichier] = module
            spec.loader.exec_module(module)
            
            # Mettre en cache le module
            self.modules_cache[nom_fichier] = module
            
            return module
        except Exception as e:
            print(f"Erreur lors de l'importation du module {nom_fichier}: {e}")
            print(traceback.format_exc())
            return None

    def get_analysis_function(self, analysis_name):
        """Obtient la fonction d'analyse correspondant au nom"""
        function_map = {
            "Force Musculaire": self.lancer_activite_musculaire,
            "Translations AP-IS": self.lancer_translations_apis,
            "Ratio d'Instabilité": self.lancer_ratio_instabilite,
            "Analyse des Résultats": self.lancer_analyse_resultats
        }
        
        return function_map.get(analysis_name, None)

    def lancer_activite_musculaire(self, selection_file=None):
        try:
            import os
            os.chdir(r"C:\Users\p0137717\Documents\Python")
            
            # Importer le module force musculaire 
            module = self.importer_module("Activite_musculaire_graph")
            if module is not None:
                # Injecter le fichier de sélection si disponible
                if selection_file and os.path.exists(selection_file):
                    module.SELECTED_RESULTS_FILE = selection_file
                
                if hasattr(module, 'generate_all_difference_graphs'):
                    module.generate_all_difference_graphs(module.Muscles_Main)
        except Exception as e:
            print(f"Erreur lors de l'exécution de l'analyse de l'activité musculaire: {e}")
            print(traceback.format_exc())

    def lancer_translations_apis(self, selection_file=None):
        try:
            import os
            os.chdir(r"C:\Users\p0137717\Documents\Python")
            
            # Importer le module Translation_APIS_Graph
            module = self.importer_module("Translation_APIS_Graph")
            if module is not None:
                # Injecter le fichier de sélection si disponible
                if selection_file and os.path.exists(selection_file):
                    module.SELECTED_RESULTS_FILE = selection_file
                
                # Vérifier si le module a une fonction main()
                if hasattr(module, 'main'):
                    module.main()
        except Exception as e:
            print(f"Erreur lors de l'exécution de Translation_APIS_Graph: {e}")
            print(traceback.format_exc())

    def lancer_ratio_instabilite(self, selection_file=None):
        try:
            import os
            os.chdir(r"C:\Users\p0137717\Documents\Python")
            
            # Importer le module Ratio_instabilite_graph
            module = self.importer_module("Ratio_instabilite_graph")
            if module is not None:
                # Injecter le fichier de sélection si disponible
                if selection_file and os.path.exists(selection_file):
                    module.SELECTED_RESULTS_FILE = selection_file
                
                # Vérifier si le module a une fonction analyze_instability_ratio_all_cases()
                if hasattr(module, 'analyze_instability_ratio_all_cases'):
                    module.analyze_instability_ratio_all_cases()
        except Exception as e:
            print(f"Erreur lors de l'exécution du ratio d'instabilité: {e}")
            print(traceback.format_exc())

    def lancer_analyse_resultats(self, selection_file=None):
        try:
            import os
            os.chdir(r"C:\Users\p0137717\Documents\Python")
            
            # Importer le module SoS_analyse_resultats
            module = self.importer_module("SoS_analyse_resultats")
            if module is not None:
                # Injecter le fichier de sélection si disponible
                if selection_file and os.path.exists(selection_file):
                    module.SELECTED_RESULTS_FILE = selection_file
                
                # Vérifier si le module a une fonction main()
                if hasattr(module, 'main'):
                    module.main()
        except Exception as e:
            print(f"Erreur lors de l'exécution de l'analyse des résultats: {e}")
            print(traceback.format_exc())
    
    def create_menu(self):
        """Crée la barre de menu principale"""
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        
        # Menu Fichier
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Fichier", menu=file_menu)
        
        file_menu.add_command(label="Ouvrir répertoire de travail", command=self.change_working_directory)
        file_menu.add_command(label="Enregistrer toutes les figures", command=self.save_all_figures)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.root.destroy, accelerator="Ctrl+Q")
        
        # Menu Analyse
        analysis_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Analyse", menu=analysis_menu)
        
        analysis_menu.add_command(label="Analyse de la force musculaire", 
                                  command=lambda: self.run_analysis_with_selection("Force Musculaire", self.lancer_activite_musculaire), 
                                  accelerator="Ctrl+1")
        analysis_menu.add_command(label="Translations AP-IS", 
                                  command=lambda: self.run_analysis_with_selection("Translations AP-IS", self.lancer_translations_apis), 
                                  accelerator="Ctrl+2")
        analysis_menu.add_command(label="Ratio d'instabilité", 
                                  command=lambda: self.run_analysis_with_selection("Ratio d'Instabilité", self.lancer_ratio_instabilite), 
                                  accelerator="Ctrl+3")
        analysis_menu.add_command(label="Analyse globale des résultats", 
                                  command=lambda: self.run_analysis_with_selection("Analyse des Résultats", self.lancer_analyse_resultats), 
                                  accelerator="Ctrl+4")
        
        # Menu Thème
        theme_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Thème", menu=theme_menu)
        
        theme_menu.add_command(label="Thème clair", command=lambda: self.apply_theme("light"))
        theme_menu.add_command(label="Thème sombre", command=lambda: self.apply_theme("dark"))
        
        # Menu Aide
        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Aide", menu=help_menu)
        
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="À propos", command=self.show_about)
    
    def setup_keyboard_shortcuts(self):
        """Configure les raccourcis clavier"""
        self.root.bind("<Control-q>", lambda e: self.root.destroy())
        self.root.bind("<Control-1>", lambda e: self.run_analysis_with_selection("Force Musculaire", self.lancer_activite_musculaire))
        self.root.bind("<Control-2>", lambda e: self.run_analysis_with_selection("Translations AP-IS", self.lancer_translations_apis))
        self.root.bind("<Control-3>", lambda e: self.run_analysis_with_selection("Ratio d'Instabilité", self.lancer_ratio_instabilite))
        self.root.bind("<Control-4>", lambda e: self.run_analysis_with_selection("Analyse des Résultats", self.lancer_analyse_resultats))
        self.root.bind("<Control-s>", lambda e: self.save_all_figures())
    
    def change_working_directory(self):
        """Change le répertoire de travail"""
        new_dir = filedialog.askdirectory(
            initialdir=os.getcwd(),
            title="Sélectionner le répertoire de travail"
        )
        if new_dir:
            try:
                os.chdir(new_dir)
                messagebox.showinfo("Information", f"Répertoire de travail changé pour:\n{new_dir}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de changer le répertoire: {e}")
    
    def change_colormap(self, cmap_name):
        """Change la palette de couleurs par défaut"""
        self.default_cmap = cmap_name
        messagebox.showinfo("Information", f"Palette de couleurs changée pour: {cmap_name}")
        plt.rcParams['image.cmap'] = cmap_name
    
    def change_plot_style(self, style_name):
        """Change le style des graphiques"""
        try:
            plt.style.use(style_name)
            self.default_style = style_name
            messagebox.showinfo("Information", f"Style de graphique changé pour: {style_name}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de changer le style: {e}")
    
    def save_figure(self, fig, tab_title):
        """
        Sauvegarde la figure actuelle dans un fichier
        """
        # Créer un sous-répertoire pour le type d'analyse
        save_dir = os.path.join(self.default_save_dir, self.current_analysis.replace(" ", "_"))
        if not os.path.exists(save_dir):
            try:
                os.makedirs(save_dir)
            except Exception as e:
                print(f"Erreur lors de la création du répertoire: {e}")
                save_dir = self.default_save_dir
        
        # Créer un nom de fichier par défaut
        default_filename = f"{self.current_analysis}_{tab_title.replace(' ', '_')}.png"
        
        # Ouvrir la boîte de dialogue de sauvegarde
        filename = filedialog.asksaveasfilename(
            initialdir=save_dir,
            initialfile=default_filename,
            defaultextension=".png",
            filetypes=[
                ("Images PNG", "*.png"),
                ("Images JPEG", "*.jpg"),
                ("Images SVG", "*.svg"),
                ("Images PDF", "*.pdf"),
                ("Tous les fichiers", "*.*")
            ],
            title="Enregistrer la figure"
        )
        
        if filename:
            try:
                # Déterminer le format en fonction de l'extension
                format_extension = os.path.splitext(filename)[1][1:].lower()
                
                # Sauvegarder avec la résolution appropriée
                fig.savefig(filename, format=format_extension, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Sauvegarde réussie", f"Figure enregistrée sous {filename}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'enregistrement: {e}")
    
    def save_all_figures(self):
        """
        Sauvegarde toutes les figures de l'analyse actuelle
        """
        if not hasattr(self, 'current_analysis') or self.current_analysis not in self.analysis_figures:
            messagebox.showinfo("Information", "Aucune figure à sauvegarder.")
            return
        
        # Demander le répertoire de destination
        save_dir = filedialog.askdirectory(
            initialdir=self.default_save_dir,
            title="Choisir le répertoire pour enregistrer toutes les figures"
        )
        
        if not save_dir:
            return
        
        # Créer un sous-répertoire pour cette analyse
        analysis_dir = os.path.join(save_dir, self.current_analysis.replace(" ", "_"))
        if not os.path.exists(analysis_dir):
            try:
                os.makedirs(analysis_dir)
            except Exception as e:
                print(f"Erreur lors de la création du répertoire: {e}")
                analysis_dir = save_dir
        
        # Enregistrer chaque figure
        success_count = 0
        error_count = 0
        for fig_id, fig in self.analysis_figures[self.current_analysis]:
            try:
                filename = os.path.join(analysis_dir, f"{self.current_analysis}_Fig{fig_id}.png")
                fig.savefig(filename, dpi=300, bbox_inches='tight')
                success_count += 1
            except Exception as e:
                print(f"Erreur lors de l'enregistrement de la figure {fig_id}: {e}")
                error_count += 1
        
        # Afficher un message de réussite
        if error_count == 0:
            messagebox.showinfo("Sauvegarde réussie", f"{success_count} figure(s) enregistrée(s) dans {analysis_dir}")
        else:
            messagebox.showwarning("Sauvegarde partielle", 
                                  f"{success_count} figure(s) enregistrée(s), {error_count} erreur(s) dans {analysis_dir}")
    
    def show_documentation(self):
        """Affiche la documentation de l'application"""
        doc_window = tk.Toplevel(self.root)
        doc_window.title("Documentation")
        doc_window.geometry("800x600")
        
        # Créer un widget texte pour afficher la documentation
        doc_text = scrolledtext.ScrolledText(doc_window, wrap=tk.WORD)
        doc_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Documentation
        doc_content = """# Documentation Lanceur d'Analyses AnyBody

## Introduction
Cette application permet d'exécuter différentes analyses sur les données exportées du logiciel AnyBody et de visualiser les résultats sous forme de graphiques.

## Analyses disponibles
1. **Analyse de la force musculaire** - Affiche les résultats de force musculaire calculés par AnyBody.
2. **Translations AP-IS** - Analyse les translations antéro-postérieures et inféro-supérieures des articulations.
3. **Ratio d'instabilité** - Calcule et affiche les ratios d'instabilité selon les simulations AnyBody.
4. **Analyse globale des résultats** - Analyse avancée des résultats de simulation.

## Sélection des simulations
- Avant chaque analyse, vous pouvez sélectionner les simulations spécifiques à inclure
- Utilisez la recherche pour trouver rapidement des simulations par nom
- Filtrez par préfixe pour regrouper des simulations similaires
- Vous pouvez modifier votre sélection à tout moment pendant l'analyse

## Visualisation
- Toutes les figures sont générées dans des onglets séparés
- Les figures peuvent être personnalisées individuellement
- Les figures peuvent être exportées individuellement ou toutes ensemble
- La comparaison de figures permet d'évaluer plusieurs résultats simultanément

## Raccourcis clavier
- Ctrl+1 : Lancer l'analyse de la force musculaire
- Ctrl+2 : Lancer l'analyse des translations AP-IS
- Ctrl+3 : Lancer l'analyse du ratio d'instabilité
- Ctrl+4 : Lancer l'analyse des résultats
- Ctrl+S : Enregistrer toutes les figures
- Ctrl+Q : Quitter l'application

## Organisation des données
Les données doivent être exportées d'AnyBody dans le format attendu par les scripts Python correspondants.
Pour plus d'informations sur l'exportation des données d'AnyBody, consulter la documentation du logiciel.
"""
        
        doc_text.insert(tk.END, doc_content)
        doc_text.config(state='disabled')  # Rendre le texte non éditable
    
    def show_about(self):
        """Affiche la fenêtre À propos"""
        about_window = tk.Toplevel(self.root)
        about_window.title("À propos")
        about_window.geometry("400x300")
        about_window.resizable(False, False)
        
        # Frame pour centrer le contenu
        frame = ttk.Frame(about_window)
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Titre
        ttk.Label(frame, text="Lanceur d'Analyses AnyBody", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        # Version
        ttk.Label(frame, text="Version 1.3.0").pack()
        
        # Date
        current_date = datetime.datetime.now().strftime("%d/%m/%Y")
        ttk.Label(frame, text=f"Date: {current_date}").pack(pady=5)
        
        # Description
        description = "Application d'analyse et de visualisation des résultats de simulations biomécaniques du logiciel AnyBody avec sélection personnalisée des simulations."
        ttk.Label(frame, text=description, wraplength=350).pack(pady=10)
        
        # Contact
        ttk.Label(frame, text="© 2025 - LIO Biomécanique").pack(pady=5)
        
        # Bouton fermer
        ttk.Button(frame, text="Fermer", command=about_window.destroy).pack(pady=10)
    
    def compare_figures(self):
        """Ouvre une fenêtre pour comparer des figures côte à côte"""
        if not hasattr(self, 'current_analysis') or self.current_analysis not in self.analysis_figures:
            messagebox.showinfo("Information", "Aucune figure disponible pour la comparaison.")
            return
        
        # Créer une fenêtre pour la comparaison
        compare_window = tk.Toplevel(self.root)
        compare_window.title(f"Comparaison de figures - {self.current_analysis}")
        compare_window.geometry("1200x800")
        
        # Créer un cadre pour contenir les figures
        compare_frame = ttk.Frame(compare_window)
        compare_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Créer une grille pour les figures (2x2)
        figures = self.analysis_figures[self.current_analysis]
        for i, (fig_id, fig) in enumerate(figures[:4]):  # Limiter à 4 figures
            row = i // 2
            col = i % 2
            
            # Créer un cadre pour cette figure
            fig_frame = ttk.Frame(compare_frame)
            fig_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            # Afficher la figure
            canvas = FigureCanvasTkAgg(fig, master=fig_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)
            
            # Ajouter une étiquette
            ttk.Label(fig_frame, text=f"Figure {fig_id}").pack()
        
        # Configurer les poids de la grille
        compare_frame.columnconfigure(0, weight=1)
        compare_frame.columnconfigure(1, weight=1)
        compare_frame.rowconfigure(0, weight=1)
        compare_frame.rowconfigure(1, weight=1)
        
        # Bouton pour fermer
        ttk.Button(compare_window, text="Fermer", command=compare_window.destroy).pack(pady=10)

    def customize_figure(self, fig, tab_title):
        """Ouvre une fenêtre pour personnaliser la figure"""
        if not fig:
            return
            
        # Créer une fenêtre pour la personnalisation
        customize_window = tk.Toplevel(self.root)
        customize_window.title(f"Personnaliser {tab_title}")
        customize_window.geometry("500x400")
        
        # Cadre principal
        main_frame = ttk.Frame(customize_window)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Options de colormap
        ttk.Label(main_frame, text="Palette de couleurs:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        cmap_var = tk.StringVar(value=self.default_cmap)
        cmap_combo = ttk.Combobox(main_frame, textvariable=cmap_var, values=self.available_cmaps)
        cmap_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        # Options de style
        ttk.Label(main_frame, text="Style de graphique:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        style_var = tk.StringVar(value=self.default_style)
        style_combo = ttk.Combobox(main_frame, textvariable=style_var, values=self.available_styles)
        style_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        # Titre du graphique
        ttk.Label(main_frame, text="Titre:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        title_var = tk.StringVar(value=tab_title)
        title_entry = ttk.Entry(main_frame, textvariable=title_var, width=30)
        title_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        
        # Taille de police
        ttk.Label(main_frame, text="Taille de police:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        fontsize_var = tk.IntVar(value=12)
        fontsize_spin = ttk.Spinbox(main_frame, from_=8, to=24, textvariable=fontsize_var, width=5)
        fontsize_spin.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        
        # Fonction pour appliquer les changements
        def apply_changes():
            try:
                # Appliquer les changements à la figure
                with plt.style.context(style_var.get()):
                    for ax in fig.get_axes():
                        # Mettre à jour le colormap pour les heatmaps ou autres plots colorés
                        for item in ax.get_children():
                            if hasattr(item, "set_cmap"):
                                item.set_cmap(cmap_var.get())
                        
                        # Mettre à jour les textes
                        ax.set_title(ax.get_title(), fontsize=fontsize_var.get())
                        ax.set_xlabel(ax.get_xlabel(), fontsize=fontsize_var.get())
                        ax.set_ylabel(ax.get_ylabel(), fontsize=fontsize_var.get())
                    
                    # Mettre à jour le titre de la figure
                    fig.suptitle(title_var.get())
                
                # Redessiner la figure
                fig.canvas.draw_idle()
                
                # Mettre à jour le titre de l'onglet
                for i in range(self.analysis_notebook.index("end")):
                    if self.analysis_notebook.tab(i, "text") == tab_title:
                        self.analysis_notebook.tab(i, text=title_var.get())
                        break
                
                messagebox.showinfo("Succès", "Personnalisation appliquée avec succès")
                customize_window.destroy()
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la personnalisation: {e}")
        
        # Boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=15)
        
        ttk.Button(button_frame, text="Appliquer", command=apply_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Annuler", command=customize_window.destroy).pack(side=tk.LEFT, padx=5)
        
        # Configuration des colonnes
        main_frame.columnconfigure(1, weight=1)
    
    def show_current_selection(self):
        """Affiche les simulations actuellement sélectionnées"""
        if not self.selected_results or "simulations" not in self.selected_results:
            messagebox.showinfo("Information", "Aucune simulation sélectionnée.")
            return
            
        # Créer une fenêtre pour afficher la sélection
        selection_window = tk.Toplevel(self.root)
        selection_window.title("Simulations sélectionnées")
        selection_window.geometry("600x400")
        selection_window.transient(self.root)
        
        # Frame principal
        main_frame = ttk.Frame(selection_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Label d'instructions
        instructions = ttk.Label(main_frame, 
                                text=f"Simulations sélectionnées pour l'analyse {self.current_analysis}:", 
                                font=("Arial", 12, "bold"))
        instructions.pack(pady=(0, 10), anchor=tk.W)
        
        # Frame pour la liste avec scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Liste des simulations
        simulation_listbox = tk.Listbox(list_frame, 
                                      font=("Arial", 11),
                                      yscrollcommand=scrollbar.set)
        simulation_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=simulation_listbox.yview)
        
        # Remplir la liste avec les simulations sélectionnées
        for sim_name in sorted(self.selected_results["simulations"].keys()):
            simulation_listbox.insert(tk.END, sim_name)
            
        # Bouton pour fermer
        ttk.Button(main_frame, 
                  text="Fermer", 
                  command=selection_window.destroy).pack(pady=10)
        
        # Centrer la fenêtre
        selection_window.update_idletasks()
        width = selection_window.winfo_width()
        height = selection_window.winfo_height()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - width) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - height) // 2
        selection_window.geometry(f"{width}x{height}+{x}+{y}")
    
    def __del__(self):
        # Restaurer la fonction plt.show originale avant de quitter
        if hasattr(self, 'original_plt_show'):
            plt.show = self.original_plt_show


# Fonction pour modifier automatiquement les modules d'analyse
def patch_analysis_modules():
    """
    Modifie les modules d'analyse pour qu'ils utilisent les résultats sélectionnés
    
    Cette fonction crée des versions modifiées des modules d'analyse qui vont:
    1. Vérifier s'il existe un fichier de sélection temporaire
    2. Utiliser ce fichier au lieu du fichier par défaut si présent
    """
    module_paths = [
        "C:/Users/p0137717/Documents/Python/Activite_musculaire_graph.py",
        "C:/Users/p0137717/Documents/Python/Translation_APIS_Graph.py",
        "C:/Users/p0137717/Documents/Python/Ratio_instabilite_graph.py",
        "C:/Users/p0137717/Documents/Python/SoS_analyse_resultats.py"
    ]
    
    for module_path in module_paths:
        if not os.path.exists(module_path):
            continue
            
        # Lire le contenu du module
        with open(module_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Vérifier si le module a déjà été modifié
        if "SELECTED_RESULTS_FILE" in content:
            continue
            
        # Ajouter le code de gestion de la sélection
        selection_code = """
# Variable pour stocker le chemin vers un fichier de résultats sélectionnés
SELECTED_RESULTS_FILE = None

# Modification de la fonction de chargement des résultats
def _load_results_with_selection():
    import pickle
    import os
    
    # Répertoire des simulations sauvegardées
    SaveSimulationsDirectory = "C:/Users/p0137717/Documents/Python/Saved Simulations"
    
    # Si un fichier de sélection est spécifié, l'utiliser
    if SELECTED_RESULTS_FILE and os.path.exists(SELECTED_RESULTS_FILE):
        try:
            with open(SELECTED_RESULTS_FILE, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Erreur lors du chargement de la sélection: {e}")
    
    # Sinon, charger les résultats normalement
    try:
        ResultsFile = os.path.join(SaveSimulationsDirectory, "Results.pkl")
        with open(ResultsFile, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Erreur lors du chargement des résultats: {e}")
        return None
"""
        
        # Chercher où insérer le code de sélection
        import_positions = [
            content.find("import pickle"),
            content.find("from Anybody_Package"),
            content.find("import numpy"),
            content.find("import matplotlib")
        ]
        
        # Trouver la position d'insertion après le dernier import
        import_positions = [pos for pos in import_positions if pos != -1]
        if import_positions:
            insert_position = max(import_positions)
            
            # Trouver la fin de la ligne
            line_end = content.find("\n", insert_position)
            if line_end != -1:
                insert_position = line_end + 1
                
                # Insérer le code de sélection
                modified_content = content[:insert_position] + selection_code + content[insert_position:]
                
                # Remplacer le chargement des résultats
                load_patterns = [
                    "with open(ResultsFile, 'rb') as f:",
                    "Results = pickle.load(f)",
                    "SaveSimulationsDirectory = "
                ]
                
                # Chercher le bloc de chargement des résultats
                for pattern in load_patterns:
                    if pattern in modified_content:
                        pattern_pos = modified_content.find(pattern)
                        if pattern_pos != -1:
                            # Trouver le début du bloc
                            block_start = modified_content.rfind("\n", 0, pattern_pos) + 1
                            
                            # Trouver la fin du bloc (jusqu'à la ligne vide suivante)
                            block_end = pattern_pos
                            next_blank = modified_content.find("\n\n", pattern_pos)
                            if next_blank != -1:
                                block_end = next_blank
                            
                            # Remplacer le bloc par un appel à la nouvelle fonction
                            replacement = "# Charger les résultats avec gestion de la sélection\nResults = _load_results_with_selection()\n"
                            modified_content = modified_content[:block_start] + replacement + modified_content[block_end:]
                            break
                
                # Sauvegarder le module modifié
                backup_path = module_path + ".bak"
                if not os.path.exists(backup_path):
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                        
                with open(module_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)


if __name__ == "__main__":
    # Appliquer les correctifs aux modules d'analyse
    try:
        patch_analysis_modules()
    except Exception as e:
        print(f"Avertissement: Impossible de modifier les modules d'analyse: {e}")
    
    root = tk.Tk()
    app = AnalysisLauncher(root)
    root.mainloop()
