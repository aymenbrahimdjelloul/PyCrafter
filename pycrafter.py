"""
This code or file is part of 'PyCrafter' project
copyright (c) 2025, Aymen Brahim Djelloul, All rights reserved.
use of this source code is governed by MIT License that can be found on the project folder.

@author : Aymen Brahim Djelloul
version : 0.1
date : 09.06.2025
license : MIT License


"""

# IMPORTS
import os
import sys
import shutil
import tempfile
import threading
import platform
import subprocess
import webbrowser
import tempfile
import logging
from pathlib import Path
from typing import List, Optional, Callable
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from tkinter.font import Font


# Handle PyInstaller import
try:
    import PyInstaller.__main__
    from PyInstaller import log as pyi_log

    PYINSTALLER_AVAILABLE: bool = True

except ImportError:
    PYINSTALLER_AVAILABLE: bool = False


class CrafterError(Exception):
    """Custom exception for Crafter operations"""
    pass


class Const:
    """ This is the Const class containing all App constants"""

    # Declare Application constants
    author: str = "Aymen Brahim Djelloul"
    version: str = "0.1"
    date: str = "09.06.2025"
    license: str = "MIT License"

    description: tuple[str, str] = (
        "PyInstaller – Used for packaging the application into standalone executables.\n"
        "Official website: https://www.pyinstaller.org/",

        "Tkinter – Used for building the graphical user interface.\n"
        "Official documentation: https://docs.python.org/3/library/tkinter.html"
    )

    github_repo: str = "https://github.com/aymenbrahimdjelloul/PyCrafter"

    # Declare UI constants
    geometry: str = "430x600"
    caption: str = f"PyCrafter - v{version}"

    # Declare colors constants
    emoji_icon: str = "🔨"
    colors: dict[str, str] = {
        "primary": "#3498db",
        "primary_dark": "#2980b9",
        "primary_darker": "#21618c",
        "secondary": "#2c3e50",
        "text": "#34495e",
        "text_light": "#7f8c8d",
        "text_lighter": "#95a5a6",
        "background": "#ffffff",
        "background_alt": "#f8f9fa",
        "background_section": "#ecf0f1",
        "shadow": "#e3e8f0"
    }


class Crafter:
    """
    Enhanced PyInstaller wrapper to compile Python scripts to Windows executables.
    Designed for backend use with PyCraft GUI or standalone automation.
    """

    def __init__(self,
                 script: str,
                 output: Optional[str] = None,
                 icon: Optional[str] = None,
                 name: Optional[str] = None,
                 no_console: bool = False,
                 one_file: bool = True,
                 require_admin: bool = False,
                 clean_build: bool = False,
                 force_replace: bool = False,
                 optimize: bool = False,
                 hidden_imports: Optional[List[str]] = None,
                 excluded_modules: Optional[List[str]] = None,
                 data_files: Optional[List[str]] = None,
                 binary_files: Optional[List[str]] = None,
                 extra_paths: Optional[List[str]] = None,
                 progress_callback: Optional[Callable[[str], None]] = None) -> None:

        # Initialize presence of PyInstaller
        if not PYINSTALLER_AVAILABLE:
            raise CrafterError("PyInstaller is not installed. Install it using: pip install pyinstaller")

        # Check for empty script path
        if not script or not isinstance(script, str):
            raise CrafterError("Script path must be a non-empty string")

        # Check the python script
        script_path = Path(script)
        if not script_path.is_file() or script_path.suffix.lower() != ".py":
            raise CrafterError("The provided script path must point to a valid .py file.")

        self.script = script_path.resolve()
        self.output = Path(output).resolve() if output else self.script.parent
        self.icon = Path(icon).resolve() if icon else None
        self.name = name or self.script.stem
        self.no_console = no_console
        self.one_file = one_file
        self.require_admin = require_admin
        self.clean_build = clean_build
        self.force_replace = force_replace
        self.optimize = optimize
        self.progress_callback = progress_callback

        # Ensure lists are not None and filter out empty strings
        self.hidden_imports = [item.strip() for item in (hidden_imports or []) if item and item.strip()]
        self.excluded_modules = [item.strip() for item in (excluded_modules or []) if item and item.strip()]
        self.data_files = [item.strip() for item in (data_files or []) if item and item.strip()]
        self.binary_files = [item.strip() for item in (binary_files or []) if item and item.strip()]
        self.extra_paths = [item.strip() for item in (extra_paths or []) if item and item.strip()]

        # Setup logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,  # Always INFO unless expanded later
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    def build(self) -> str:
        """
        Build the executable with comprehensive error handling

        Returns:
            str: Path to the created executable

        Raises:
            CrafterError: If build fails or validation errors occur
        """
        try:
            self._log_progress("Starting build process...")

            # Validate inputs
            self._validate_inputs()

            if self.clean_build:
                self._log_progress("Cleaning temporary files...")
                self._clean_temp_files()

            # Ensure output directory exists
            self.output.mkdir(parents=True, exist_ok=True)

            exe_path = self.output / f"{self.name}.exe"
            if self.force_replace and exe_path.exists():
                self._log_progress("Removing existing executable...")
                exe_path.unlink()

            self._log_progress("Preparing PyInstaller command...")

            cmd = self._build_command()

            pyi_log.logger.setLevel(pyi_log.INFO)

            self._log_progress(f"Building {self.name} from {self.script}...")
            self.logger.info(f"PyInstaller command: {' '.join(cmd)}")

            # Run PyInstaller
            PyInstaller.__main__.run(cmd)

            # Verify the executable was created
            if exe_path.exists():
                self._log_progress(f"✅ Build complete! Executable created at: {exe_path}")
                self.logger.info(f"Executable size: {exe_path.stat().st_size / (1024 * 1024):.2f} MB")
                return str(exe_path)
            else:
                raise CrafterError("Build completed but executable file was not found.")

        except Exception as e:
            error_msg = f"Build failed: {str(e)}"
            self._log_progress(f"❌ {error_msg}")
            self.logger.error(error_msg, exc_info=self.debug)
            raise CrafterError(error_msg) from e

    def _log_progress(self, message: str):
        """Log progress to both callback and logger"""
        if self.progress_callback:
            self.progress_callback(message)
        self.logger.info(message)

    def _validate_inputs(self):
        """Validate all input parameters"""
        if not self.script.exists():
            raise CrafterError(f"Script file not found: {self.script}")

        if self.icon and not self.icon.exists():
            raise CrafterError(f"Icon file not found: {self.icon}")

        if not os.access(self.output.parent, os.W_OK):
            raise CrafterError(f"No write permission for output directory: {self.output}")

        # Validate name doesn't contain invalid characters
        invalid_chars = '<>:"/\\|?*'
        if any(char in self.name for char in invalid_chars):
            raise CrafterError(f"Executable name contains invalid characters: {invalid_chars}")

        # Validate data files and binaries exist
        for data_file in self.data_files:
            if ';' in data_file:
                src_path = data_file.split(';')[0]
                if not Path(src_path).exists():
                    raise CrafterError(f"Data file not found: {src_path}")

        for binary_file in self.binary_files:
            if ';' in binary_file:
                src_path = binary_file.split(';')[0]
                if not Path(src_path).exists():
                    raise CrafterError(f"Binary file not found: {src_path}")

    def _build_command(self) -> List[str]:
        """Build the PyInstaller command with all parameters"""
        # Create temporary directories for this build
        work_dir = Path(tempfile.mkdtemp(prefix="pyinstaller_work_"))
        spec_dir = Path(tempfile.mkdtemp(prefix="pyinstaller_spec_"))

        cmd = [
            str(self.script),
            "--name", self.name,
            "--distpath", str(self.output),
            "--workpath", str(work_dir),
            "--specpath", str(spec_dir)
        ]

        if self.icon:
            cmd.extend(["--icon", str(self.icon)])

        if self.one_file:
            cmd.append("--onefile")

        if self.no_console:
            cmd.append("--noconsole")

        if self.require_admin:
            cmd.append("--uac-admin")

        if self.optimize:
            cmd.extend(["--optimize", "2"])

        # Add hidden imports
        for item in self.hidden_imports:
            cmd.extend(["--hidden-import", item])

        # Add excluded modules
        for item in self.excluded_modules:
            cmd.extend(["--exclude-module", item])

        # Add data files
        for data in self.data_files:
            cmd.extend(["--add-data", data])

        # Add binary files
        for binary in self.binary_files:
            cmd.extend(["--add-binary", binary])

        # Add extra paths
        for path in self.extra_paths:
            cmd.extend(["--paths", path])

        return cmd

    def _clean_temp_files(self):
        """Clean temporary build and spec files."""
        try:
            # Clean spec file
            spec_file = self.script.with_suffix(".spec")
            if spec_file.exists():
                spec_file.unlink()
                self.logger.debug(f"Removed spec file: {spec_file}")

            # Clean build directories
            for folder_name in ["build", "__pycache__"]:
                folder_path = self.script.parent / folder_name
                if folder_path.exists():
                    shutil.rmtree(folder_path, ignore_errors=True)
                    self.logger.debug(f"Removed directory: {folder_path}")

            # Clean PyInstaller cache
            cache_dir = Path.home() / ".pyinstaller"
            if cache_dir.exists():
                shutil.rmtree(cache_dir, ignore_errors=True)
                self.logger.debug("Cleared PyInstaller cache")

        except Exception as e:
            warning_msg = f"Warning: Could not clean some temporary files: {e}"
            self._log_progress(warning_msg)
            self.logger.warning(warning_msg)

    def get_build_info(self) -> dict:
        """Get information about the current build configuration"""
        return {
            "script": str(self.script),
            "output_dir": str(self.output),
            "executable_name": self.name,
            "icon": str(self.icon) if self.icon else None,
            "one_file": self.one_file,
            "no_console": self.no_console,
            "require_admin": self.require_admin,
            "optimize": self.optimize,
            "hidden_imports": self.hidden_imports,
            "excluded_modules": self.excluded_modules,
            "data_files": self.data_files,
            "binary_files": self.binary_files,
            "extra_paths": self.extra_paths
        }


class PyCrafter:
    """ PyCrafter class contain the Application UI"""

    def __init__(self, root) -> None:

        # Initialize Application
        self.root = root
        self.root.title(Const.caption)
        self.root.geometry(Const.geometry)
        self.root.resizable(False, False)

        # Configure style
        self.setup_styles()

        # Variables
        self.script_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.icon_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.hidden_imports_var = tk.StringVar()
        self.excluded_modules_var = tk.StringVar()
        self.data_files_var = tk.StringVar()
        self.binary_files_var = tk.StringVar()
        self.extra_paths_var = tk.StringVar()

        # Boolean variables
        self.no_console_var = tk.BooleanVar()
        self.one_file_var = tk.BooleanVar(value=True)
        self.admin_var = tk.BooleanVar()
        self.clean_build_var = tk.BooleanVar()
        self.force_replace_var = tk.BooleanVar()
        self.optimize_var = tk.BooleanVar()

        # Set icon
        self._set_icon()

        # Set up ui
        self.setup_ui()

    def setup_styles(self) -> None:
        """Configure professional styling"""

        style = ttk.Style()

        # Configure colors and fonts
        bg_color: str = "#f8f9fa"
        card_color: str = "#ffffff"
        primary_color: str = "#0066cc"
        # success_color = "#28a745"
        text_color: str = "#333333"

        self.root.configure(bg=bg_color)

        # Configure ttk styles
        style.configure("Title.TLabel",
                        font=("Segoe UI", 16, "bold"),
                        foreground=primary_color,
                        background=bg_color)

        style.configure("Heading.TLabel",
                        font=("Segoe UI", 10, "bold"),
                        foreground=text_color,
                        background=card_color)

        style.configure("Card.TFrame",
                        background=card_color,
                        relief="solid",
                        borderwidth=1)

        style.configure("Main.TFrame",
                        background=bg_color)

        style.configure("Custom.TCheckbutton",
                        background=card_color,
                        foreground=text_color,
                        font=("Segoe UI", 9))

    @staticmethod
    def create_card_frame(parent, title):
        """Create a professional card-style frame"""
        card = ttk.Frame(parent, style="Card.TFrame", padding=15)
        if title:
            title_label = ttk.Label(card, text=title, style="Heading.TLabel")
            title_label.pack(anchor="w", pady=(0, 10))
        return card

    @staticmethod
    def create_file_selector(parent, label_text, variable, browse_command, file_types=None) -> None:
        """Create a professional file selector with label, entry, and browse button"""
        ttk.Label(parent, text=label_text, font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 3))

        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=(0, 10))

        entry = ttk.Entry(frame, textvariable=variable, font=("Segoe UI", 9))
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn = ttk.Button(frame, text="Browse", command=browse_command, width=8)
        btn.pack(side="right")

        return frame

    def setup_ui(self) -> None:
        """ This method will setup the application UI """

        # Header
        header_frame = ttk.Frame(self.root, style="Main.TFrame")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        title_label = ttk.Label(header_frame, text="PyCrafter", style="Title.TLabel")
        title_label.pack(side="left")

        subtitle_label = ttk.Label(header_frame, text="Python to EXE Compiler",
                                   font=("Segoe UI", 9), foreground="#666666")
        subtitle_label.pack(side="left", padx=(10, 0), anchor="s", pady=(0, 2))

        # Main container with scrolling
        main_container = ttk.Frame(self.root, style="Main.TFrame")
        main_container.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Create scrollable area
        canvas = tk.Canvas(main_container, bg="#f8f9fa", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style="Main.TFrame")

        scrollable_frame.bind("<Configure>",
                              lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.root.bind_all("<MouseWheel>", _on_mousewheel)

        # Content sections
        self.create_input_section(scrollable_frame)
        self.create_options_section(scrollable_frame)
        self.create_advanced_section(scrollable_frame)

        # Bottom action bar
        self.create_action_bar()

    def create_input_section(self, parent):
        """Create the input files section"""
        card = self.create_card_frame(parent, "Input & Output")
        card.pack(fill="x", pady=(0, 15))

        # Python script
        self.create_file_selector(card, "Python Script *", self.script_var,
                                  self.browse_script, [("Python files", "*.py")])

        # Output directory
        self.create_file_selector(card, "Output Directory", self.output_var,
                                  self.browse_output)

        # Executable name
        ttk.Label(card, text="Executable Name", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 3))
        ttk.Entry(card, textvariable=self.name_var, font=("Segoe UI", 9)).pack(fill="x", pady=(0, 10))

        # Icon
        self.create_file_selector(card, "Icon File", self.icon_var,
                                  self.browse_icon, [("Icon files", "*.ico"), ("Image files", "*.png;*.jpg;*.jpeg")])

    def create_options_section(self, parent):
        """Create the build options section"""
        card = self.create_card_frame(parent, "Build Options")
        card.pack(fill="x", pady=(0, 15))

        # Create two columns for checkboxes
        options_frame = ttk.Frame(card)
        options_frame.pack(fill="x")

        left_col = ttk.Frame(options_frame, style="Card.TFrame")
        left_col.pack(side="left", fill="x", expand=True, padx=(0, 10))

        right_col = ttk.Frame(options_frame, style="Card.TFrame")
        right_col.pack(side="right", fill="x", expand=True)

        # Left column options
        ttk.Checkbutton(left_col, text="Hide Console Window",
                        variable=self.no_console_var, style="Custom.TCheckbutton").pack(anchor="w", pady=2)
        ttk.Checkbutton(left_col, text="Create Single File",
                        variable=self.one_file_var, style="Custom.TCheckbutton").pack(anchor="w", pady=2)
        ttk.Checkbutton(left_col, text="Ask Admin Privileges",
                        variable=self.admin_var, style="Custom.TCheckbutton").pack(anchor="w", pady=2)

        # Right column options
        ttk.Checkbutton(right_col, text="Clean Build Directory",
                        variable=self.clean_build_var, style="Custom.TCheckbutton").pack(anchor="w", pady=2)
        ttk.Checkbutton(right_col, text="Force Replace Existing",
                        variable=self.force_replace_var, style="Custom.TCheckbutton").pack(anchor="w", pady=2)
        ttk.Checkbutton(right_col, text="Optimize Code",
                        variable=self.optimize_var, style="Custom.TCheckbutton").pack(anchor="w", pady=2)

    def create_advanced_section(self, parent):
        """Create the advanced options section"""
        card = self.create_card_frame(parent, "Advanced Options")
        card.pack(fill="x", pady=(0, 15))

        # Hidden imports
        ttk.Label(card, text="Hidden Imports", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 3))
        ttk.Label(card, text="Comma-separated module names that PyInstaller might miss",
                  font=("Segoe UI", 8), foreground="#666666").pack(anchor="w", pady=(0, 3))
        ttk.Entry(card, textvariable=self.hidden_imports_var, font=("Segoe UI", 9)).pack(fill="x", pady=(0, 10))

        # Excluded modules
        ttk.Label(card, text="Excluded Modules", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 3))
        ttk.Label(card, text="Comma-separated module names to exclude from the build",
                  font=("Segoe UI", 8), foreground="#666666").pack(anchor="w", pady=(0, 3))
        ttk.Entry(card, textvariable=self.excluded_modules_var, font=("Segoe UI", 9)).pack(fill="x", pady=(0, 10))

        # Data files
        ttk.Label(card, text="Data Files", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 3))
        ttk.Label(card, text="Comma-separated paths to data files to include",
                  font=("Segoe UI", 8), foreground="#666666").pack(anchor="w", pady=(0, 3))
        ttk.Entry(card, textvariable=self.data_files_var, font=("Segoe UI", 9)).pack(fill="x", pady=(0, 10))

        # Binary files
        ttk.Label(card, text="Binary Files", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 3))
        ttk.Label(card, text="Comma-separated paths to binary files to include",
                  font=("Segoe UI", 8), foreground="#666666").pack(anchor="w", pady=(0, 3))
        ttk.Entry(card, textvariable=self.binary_files_var, font=("Segoe UI", 9)).pack(fill="x", pady=(0, 10))

        # Extra paths
        ttk.Label(card, text="Extra Paths", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 3))
        ttk.Label(card, text="Comma-separated additional paths to search for imports",
                  font=("Segoe UI", 8), foreground="#666666").pack(anchor="w", pady=(0, 3))
        ttk.Entry(card, textvariable=self.extra_paths_var, font=("Segoe UI", 9)).pack(fill="x", pady=(0, 20))

    def create_action_bar(self):
        """Create the bottom action bar with buttons"""
        action_frame = ttk.Frame(self.root, style="Main.TFrame")
        action_frame.pack(side="bottom", fill="x", padx=20, pady=(10, 20))

        # Status indicator
        status_frame = ttk.Frame(action_frame, style="Main.TFrame")
        status_frame.pack(fill="x", pady=(0, 10))

        if PYINSTALLER_AVAILABLE:
            status_color = "#28a745"
            status_text = "✓ PyCrafter is ready"
        else:
            status_color = "#dc3545"
            status_text = "✗ PyCrafter not found"

        status_label = tk.Label(status_frame, text=status_text,
                                fg=status_color, bg="#f8f9fa",
                                font=("Segoe UI", 9))
        status_label.pack(side="left")

        # Buttons
        button_frame = ttk.Frame(action_frame, style="Main.TFrame")
        button_frame.pack(fill="x")

        about_btn = ttk.Button(button_frame, text="About", command=self.show_about, width=8)
        about_btn.pack(side="left")

        # Build button (styled with tk.Button for color)
        build_btn = tk.Button(button_frame, text="Build Executable",
                              command=self.build_exe,
                              bg="#28a745", fg="white",
                              font=("Segoe UI", 10, "bold"),
                              relief="flat", borderwidth=0,
                              padx=20, pady=10,
                              cursor="hand2")
        build_btn.pack(side="right", fill="x", expand=True, padx=(10, 0))

        # Hover effects for build button
        def on_enter(e) -> None:
            build_btn.configure(bg="#218838")

        def on_leave(e) -> None:
            build_btn.configure(bg="#28a745")

        build_btn.bind("<Enter>", on_enter)
        build_btn.bind("<Leave>", on_leave)

    def browse_script(self) -> None:
        """ This method will borse the script"""

        filename = filedialog.askopenfilename(
            title="Select Python Script",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if filename:
            self.script_var.set(filename)
            if not self.name_var.get():
                self.name_var.set(Path(filename).stem)
            if not self.output_var.get():
                self.output_var.set(str(Path(filename).parent))

    def browse_output(self) -> None:
        """ This method will borse the output path"""

        dirname = filedialog.askdirectory(title="Select Output Directory")
        if dirname:
            self.output_var.set(dirname)

    def browse_icon(self) -> None:
        """ This method will borse the icon path"""

        filename = filedialog.askopenfilename(
            title="Select Icon File",
            filetypes=[("Icon files", "*.ico"), ("PNG files", "*.png"),
                       ("JPEG files", "*.jpg"), ("All files", "*.*")]
        )
        if filename:
            self.icon_var.set(filename)

    def show_about(self) -> None:
        """ This method will show the about section"""

        about = AboutDialog(self.root)
        about.show()

    def _set_icon(self) -> None:
        """Sets the application icon, works in both PyCharm and EXE."""
        try:
            # Determine the base path
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))

            # Try to load icon normally
            self.icon_path = os.path.join(base_path, 'icon.ico')
            if os.path.exists(self.icon_path):
                self.root.iconbitmap(self.icon_path)
                return

            # Fallback: Embed icon data directly
            if hasattr(self, '_icon_data'):
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.ico') as tmp:
                    tmp.write(self._icon_data)
                    tmp_path = tmp.name
                self.root.iconbitmap(tmp_path)
                # Schedule cleanup
                self.root.after(1000, lambda: os.unlink(tmp_path) if os.path.exists(tmp_path) else None)

        except Exception as e:
            print(f"Failed to set app icon: {e}")
            self.icon_path = None

    def _apply_icon(self, window: tk.Toplevel) -> None:
        """Applies the main window's icon to a dialog window, works in both PyCharm and EXE."""
        try:
            # Method 1: Try using the stored icon path (works in PyCharm)
            if hasattr(self, 'icon_path') and self.icon_path and os.path.exists(self.icon_path):
                window.iconbitmap(self.icon_path)
                return

            # Method 2: Try using sys._MEIPASS (works in EXE)
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))

            icon_path = os.path.join(base_path, 'images', 'icon.ico')
            if os.path.exists(icon_path):
                window.iconbitmap(icon_path)
                return

            # Method 3: Try using a temporary file (fallback)
            if hasattr(self, '_icon_data'):
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.ico') as tmp:
                    tmp.write(self._icon_data)
                    tmp_path = tmp.name
                window.iconbitmap(tmp_path)
                # Schedule cleanup
                window.after(1000, lambda: os.unlink(tmp_path) if os.path.exists(tmp_path) else None)

        except Exception as e:
            print(f"Could not set dialog icon: {e}")

    @staticmethod
    def parse_comma_separated(text: str) -> Optional[List[str]]:
        """ This method will parse comma separated string"""

        if not text.strip():
            return None
        return [item.strip() for item in text.split(",") if item.strip()]

    def build_exe(self) -> None:
        """ This method will build the executable"""

        if not self.script_var.get():
            messagebox.showerror("Validation Error", "Please select a Python script to compile.")
            return

        if not PYINSTALLER_AVAILABLE:
            messagebox.showerror("PyInstaller Error",
                                 "PyInstaller is not available. Please install it using:\npip install pyinstaller")
            return

        # Show building dialog
        building_dialog = self.show_building_dialog()

        # Prepare parameters
        script = self.script_var.get()
        output = self.output_var.get() if self.output_var.get() else None
        icon = self.icon_var.get() if self.icon_var.get() else None
        name = self.name_var.get() if self.name_var.get() else None
        no_console = self.no_console_var.get()
        one_file = self.one_file_var.get()
        admin = self.admin_var.get()
        clean_build = self.clean_build_var.get()
        force_replace = self.force_replace_var.get()
        optimize = self.optimize_var.get()
        hidden_imports = self.parse_comma_separated(self.hidden_imports_var.get())
        excluded_modules = self.parse_comma_separated(self.excluded_modules_var.get())
        data_files = self.parse_comma_separated(self.data_files_var.get())
        binary_files = self.parse_comma_separated(self.binary_files_var.get())
        extra_paths = self.parse_comma_separated(self.extra_paths_var.get())

        # Build command
        cmd: list[str] = ["pyinstaller"]

        if one_file:
            cmd.append("--onefile")
        if no_console:
            cmd.append("--noconsole")
        if admin:
            cmd.append("--uac-admin")
        if clean_build:
            cmd.append("--clean")
        if force_replace:
            cmd.append("--noconfirm")
        if optimize:
            cmd.append("--optimize=2")

        if output:
            cmd.extend(["--distpath", output])
        if icon:
            cmd.extend(["--icon", icon])
        if name:
            cmd.extend(["--name", name])

        if hidden_imports:
            for module in hidden_imports:
                cmd.extend(["--hidden-import", module])

        if excluded_modules:
            for module in excluded_modules:
                cmd.extend(["--exclude-module", module])

        if data_files:
            for file_path in data_files:
                cmd.extend(["--add-data", f"{file_path};."])

        if binary_files:
            for file_path in binary_files:
                cmd.extend(["--add-binary", f"{file_path};."])

        if extra_paths:
            for path in extra_paths:
                cmd.extend(["--paths", path])

        cmd.append(script)

        def run_build() -> None:
            """Optimized build function with explorer integration"""
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(script).parent)
                building_dialog.destroy()

                if result.returncode == 0:
                    output_path = Path(output) if output else Path(script).parent
                    show_success_with_explorer(output_path)
                else:
                    show_build_error()

            except Exception as e:
                building_dialog.destroy()
                messagebox.showerror("Build Error", f"Build failed: {str(e)}")

        def show_success_with_explorer(output_path: Path) -> None:
            """ This method will show the success dialog widget"""


            def open_explorer():
                """Cross-platform file explorer opener"""
                try:
                    path_str = str(output_path.resolve())
                    system = platform.system()

                    if system == "Windows":
                        os.startfile(path_str)
                    elif system == "Darwin":  # macOS
                        subprocess.Popen(["open", path_str])
                    else:  # Linux and others
                        subprocess.Popen(["xdg-open", path_str])
                except Exception as e:
                    messagebox.showerror("Error", f"Cannot open explorer: {e}")

            def close_dialog() -> None:
                """ This function will close the dialog"""
                dialog.destroy()

            # Create optimized dialog
            dialog = tk.Toplevel(self.root)
            dialog.title("Build Successful")
            dialog.geometry("420x240")
            dialog.resizable(False, False)
            self._apply_icon(dialog)  # Apply the icon
            dialog.transient(self.root)
            dialog.grab_set()

            # Center dialog
            # dialog.update_idletasks()

            x: int = (dialog.winfo_screenwidth() - 420) // 2
            y: int = (dialog.winfo_screenheight() - 180) // 2

            dialog.geometry(f"420x280+{x}+{y}")

            # Main container
            main = tk.Frame(dialog, padx=20, pady=15)
            main.pack(fill="both", expand=True)

            # Header with icon
            header = tk.Frame(main)
            header.pack(fill="x", pady=(0, 15))

            tk.Label(header, text="✅", font=("Segoe UI", 20)).pack(side="left")
            tk.Label(header, text="Build Successful!",
                     font=("Segoe UI", 14, "bold"),
                     fg="#2e7d32").pack(side="left", padx=(10, 0))

            # Message
            tk.Label(main, text="Your executable has been created successfully!",
                     font=("Segoe UI", 10)).pack(pady=(0, 10))

            # Path display
            path_frame = tk.Frame(main, bg="#f8f9fa", relief="solid", bd=1)
            path_frame.pack(fill="x", pady=(0, 15))

            tk.Label(path_frame, text="Output:", font=("Segoe UI", 8, "bold"),
                     bg="#f8f9fa").pack(anchor="w", padx=8, pady=(5, 0))
            tk.Label(path_frame, text=str(output_path), font=("Segoe UI", 8),
                     fg="#0066cc", bg="#f8f9fa", wraplength=380).pack(anchor="w", padx=8, pady=(0, 5))

            # Buttons
            btn_frame = tk.Frame(main)
            btn_frame.pack(fill="x")

            # Explorer button - primary action
            explorer_btn = tk.Button(btn_frame, text="📂 Open in Explorer",
                                     command=open_explorer,
                                     bg="#4CAF50", fg="white",
                                     font=("Segoe UI", 10, "bold"),
                                     relief="flat", cursor="hand2",
                                     padx=20, pady=8)
            explorer_btn.pack(side="left")

            # Close button
            close_btn = tk.Button(btn_frame, text="Close",
                                  command=close_dialog,
                                  bg="#757575", fg="white",
                                  font=("Segoe UI", 10),
                                  relief="flat", cursor="hand2",
                                  padx=20, pady=8)
            close_btn.pack(side="right")

            # Optimized hover effects
            def setup_hover(button, normal_color, hover_color):
                button.bind("<Enter>", lambda e: button.config(bg=hover_color))
                button.bind("<Leave>", lambda e: button.config(bg=normal_color))

            setup_hover(explorer_btn, "#4CAF50", "#45a049")
            setup_hover(close_btn, "#757575", "#616161")

            # Keyboard shortcuts
            dialog.bind("<Return>", lambda e: open_explorer())
            dialog.bind("<Escape>", lambda e: close_dialog())
            dialog.focus_set()

        def show_build_error() -> None:
            """Minimalist build error dialog"""

            self._apply_icon(dialog)  # Apply the icon

            # Create minimal dialog
            dialog = tk.Toplevel(self.root)
            dialog.title("Build Failed")
            dialog.geometry("350x150")
            dialog.resizable(False, False)
            dialog.configure(bg="#f8f8f8")
            dialog.transient(self.root)
            dialog.grab_set()

            # Center dialog
            dialog.update_idletasks()
            x: int = (dialog.winfo_screenwidth() - 350) // 2
            y: int = (dialog.winfo_screenheight() - 150) // 2
            dialog.geometry(f"350x150+{x}+{y}")

            # Content frame
            frame = tk.Frame(dialog, bg="#f8f8f8", padx=20, pady=20)
            frame.pack(fill="both", expand=True)

            # Error message
            tk.Label(frame, text="❌ Build Failed",
                     font=("Segoe UI", 12, "bold"),
                     fg="#d32f2f", bg="#f8f8f8").pack(pady=(0, 10))

            tk.Label(frame, text="The build process encountered an error.",
                     font=("Segoe UI", 9),
                     fg="#333", bg="#f8f8f8").pack(pady=(0, 15))

            # OK button
            tk.Button(frame, text="OK",
                      command=dialog.destroy,
                      bg="#e53e3e", fg="white",
                      font=("Segoe UI", 9),
                      relief="flat",
                      padx=30, pady=6).pack()

            # Keyboard shortcut
            dialog.bind("<Return>", lambda e: dialog.destroy())
            dialog.bind("<Escape>", lambda e: dialog.destroy())
            dialog.focus_set()

        def open_output_folder(path: Path) -> None:
            """Standalone function to open output folder - can be used elsewhere"""
            try:
                path_str = str(path.resolve())
                system = platform.system()

                commands = {
                    "Windows": lambda: os.startfile(path_str),
                    "Darwin": lambda: subprocess.Popen(["open", path_str]),
                    "Linux": lambda: subprocess.Popen(["xdg-open", path_str])
                }

                if system in commands:
                    commands[system]()
                else:
                    # Fallback for other systems
                    subprocess.Popen(["xdg-open", path_str])

            except Exception as e:
                messagebox.showerror("Explorer Error", f"Cannot open folder: {e}")

        # Start optimized build thread
        threading.Thread(target=run_build, daemon=True).start()

    def show_building_dialog(self) -> tk.Toplevel:
        """Show an enhanced building progress dialog centered on parent window"""


        dialog = tk.Toplevel(self.root)
        dialog.title("PyCrafter - Building Executable")
        self._apply_icon(dialog)  # Apply the icon
        dialog.geometry("400x180")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # Modern styling
        dialog.configure(bg="#f8f9fa")

        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        parent_width = self.root.winfo_width()
        parent_height = self.root.winfo_height()

        dialog_width: int = 400
        dialog_height: int = 250

        # Calculate center position relative to parent
        x: int = parent_x + (parent_width - dialog_width) // 2
        y: int = parent_y + (parent_height - dialog_height) // 2

        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

        # Main container with the subtle border
        main_frame = tk.Frame(dialog, bg="#ffffff", relief="solid", bd=1)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Content frame
        content_frame = tk.Frame(main_frame, bg="#ffffff")
        content_frame.pack(fill="both", expand=True, padx=25, pady=20)

        # Icon or visual indicator (using Unicode symbols)
        icon_label = tk.Label(content_frame, text="⚙️",
                              font=("Segoe UI", 24), bg="#ffffff")
        icon_label.pack(pady=(0, 15))

        # Main title
        title_label = tk.Label(content_frame,
                               text="Compiling Your Application",
                               font=("Segoe UI", 14, "bold"),
                               fg="#2c3e50",
                               bg="#ffffff")
        title_label.pack(pady=(0, 8))

        # Progress bar with modern styling
        progress_frame = tk.Frame(content_frame, bg="#ffffff")
        progress_frame.pack(fill="x", pady=(0, 15))

        # Configure progress bar style first
        style = ttk.Style()

        try:
            # Try to configure custom style, fallback to default if it fails
            style.configure("Custom.Horizontal.TProgressbar",
                            background="#3498db",
                            troughcolor="#ecf0f1",
                            borderwidth=1,
                            relief="flat")
            progress_style = "Custom.Horizontal.TProgressbar"
        except Exception:
            progress_style = "Horizontal.TProgressbar"

        progress = ttk.Progressbar(progress_frame,
                                   mode='indeterminate',
                                   length=300,
                                   style=progress_style)
        progress.pack()
        progress.start(10)  # Start animation immediately

        # Status text with better messaging
        status_label = tk.Label(content_frame,
                                text="Analyzing dependencies and bundling resources...\nThis may take a few moments.",
                                font=("Segoe UI", 9), fg="#7f8c8d", bg="#ffffff")
        status_label.pack()

        # Store progress bar reference for potential updates
        dialog.progress = progress
        dialog.status_label = status_label

        # Method to update status text
        def update_status(text: str):
            dialog.status_label.config(text=text)
            dialog.update_idletasks()

        # Method to close dialog properly
        def close_dialog():
            try:
                progress.stop()
                dialog.grab_release()
                dialog.destroy()
            except:
                pass

        dialog.update_status = update_status
        dialog.close_dialog = close_dialog

        # Ensure dialog stays on top and focused
        dialog.lift()
        dialog.focus_set()

        # Handle window close event (disable close button during build)
        dialog.protocol("WM_DELETE_WINDOW", lambda: None)

        # Force update to ensure everything renders
        dialog.update_idletasks()
        dialog.update()

        return dialog


class AboutDialog:
    """Optimized About Dialog for PyCrafter application"""

    # Class-level constants to reduce memory usage
    DIALOG_SIZE: str = "450x400"
    BUTTON_CONFIG: dict = {
        'font': ("Segoe UI", 11),
        'relief': "flat",
        'borderwidth': 0,
        'cursor': "hand2",
        'padx': 20,
        'pady': 8
    }

    # Color mappings for hover effects
    HOVER_COLORS: dict[str, str] = {
        'secondary': '#2980b9',
        'primary': '#c0392b'
    }

    ACTIVE_COLORS: dict[str, str] = {
        'secondary': '#21618c',
        'primary': '#922b21'
    }

    def __init__(self, parent: tk.Tk) -> None:
        self.parent = parent
        self.dialog: Optional[tk.Toplevel] = None
        self._widgets: Dict[str, tk.Widget] = {}  # Cache widgets for cleanup

    def show(self) -> None:
        """Display the about dialog"""
        if self.dialog and self.dialog.winfo_exists():
            self.dialog.lift()
            self.dialog.focus_set()
            return

        self._create_dialog()
        self._setup_layout()
        self._setup_events()
        self._show_dialog()

    def _create_dialog(self) -> None:
        """Create and configure the main dialog window"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("About - PyCraft")
        self.dialog.geometry(self.DIALOG_SIZE)
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.configure(bg=Const.colors['background_alt'])

        self._set_icon()
        self._center_dialog()

    def _set_icon(self) -> None:
        """Set the application icon"""
        try:
            icon_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                # "images",
                'icon.ico'
            )
            if os.path.exists(icon_path):
                self.dialog.iconbitmap(icon_path)
        except Exception as e:
            print(f"Failed to set app icon: {e}")

    def _center_dialog(self) -> None:
        """Center dialog relative to the parent window"""
        self.parent.update_idletasks()

        # Get parent dimensions
        px, py = self.parent.winfo_x(), self.parent.winfo_y()
        pw, ph = self.parent.winfo_width(), self.parent.winfo_height()

        # Calculate center position
        dw, dh = 450, 400
        x = px + (pw - dw) // 2
        y = py + (ph - dh) // 2

        self.dialog.geometry(f"{dw}x{dh}+{x}+{y}")

    def _setup_layout(self) -> None:
        """Set up the dialog layout efficiently"""
        # Create main container
        main_frame = tk.Frame(self.dialog, bg=Const.colors['background'])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        content_frame = tk.Frame(main_frame, bg=Const.colors['background'])
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Build layout sections
        self._create_header(content_frame)
        self._create_description(content_frame)
        self._create_action_buttons(content_frame)
        # self._create_footer()

    @staticmethod
    def _create_header(parent: tk.Frame) -> None:
        """Create title and version section"""
        # Title
        tk.Label(
            parent,
            text="PyCrafter",
            font=("Segoe UI", 16, "bold"),
            fg=Const.colors['secondary'],
            bg=Const.colors['background']
        ).pack(pady=(0, 5), anchor='center')

        # Version badge
        version_frame = tk.Frame(parent, bg=Const.colors['background_section'], bd=1)
        version_frame.pack(pady=(0, 10), anchor='center')

        tk.Label(
            version_frame,
            text=f"Version {Const.version}",
            font=("Segoe UI", 10, "bold"),
            fg=Const.colors['text'],
            bg=Const.colors['background_section']
        ).pack(padx=15, pady=6)

    def _create_description(self, parent: tk.Frame) -> None:
        """Create optimized description section"""
        desc_frame = tk.Frame(parent, bg=Const.colors['background'])
        desc_frame.pack(pady=(0, 15), anchor='center')

        # Section title
        tk.Label(
            desc_frame,
            text="Built with:",
            font=("Segoe UI", 10, "bold"),
            fg=Const.colors['text'],
            bg=Const.colors['background']
        ).pack(pady=(0, 10))

        # Process tool descriptions
        for tool_desc in Const.description:
            self._create_tool_entry(desc_frame, tool_desc)

    def _create_tool_entry(self, parent: tk.Frame, tool_desc: str) -> None:
        """Create individual tool description entry"""
        lines = tool_desc.strip().split('\n')
        main_desc = lines[0]
        url_line = lines[1] if len(lines) > 1 else ""

        tool_frame = tk.Frame(parent, bg=Const.colors['background'])
        tool_frame.pack(pady=(5, 15), anchor='center')

        # Main description
        tk.Label(tool_frame, text=main_desc, font=("Segoe UI", 11), fg=Const.colors['text'],
                 bg=Const.colors['background']).pack()

        # URL if present
        if url_line:
            url_text = url_line.replace("Official website: ", "").replace("Official documentation: ", "")
            url_label = tk.Label(
                tool_frame,
                text=url_text,
                font=("Segoe UI", 9, "italic"),
                fg=Const.colors.get('link', '#0066CC'),
                bg=Const.colors['background'],
                cursor="hand2"
            )
            url_label.pack(pady=(2, 0))
            url_label.bind("<Button-1>", lambda e, url=url_text: self._open_url(url))

    def _create_action_buttons(self, parent: tk.Frame) -> None:
        """Create optimized action buttons with resized dimensions"""
        button_frame = tk.Frame(parent, bg=Const.colors['background'])
        button_frame.pack(pady=(0, 20), anchor='center')

        # GitHub button (larger size)
        github_btn = tk.Button(
            button_frame,
            text="🔗 GitHub",
            command=lambda: self._open_url(Const.github_repo),
            bg=Const.colors['secondary'],
            fg="white",
            width=8,  # Adjust width (in characters)
            height=25,  # Adjust height (in text lines)
            **self.BUTTON_CONFIG
        )
        github_btn.pack(side='left', pady=0, padx=5)  # Added padx for spacing

        # Close button (larger size)
        close_btn = tk.Button(
            button_frame,
            text="Close",
            command=self.close,
            bg=Const.colors['primary'],
            fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            width=8,  # Adjust width (in characters)
            height=35,  # Adjust height (in text lines)
            padx=20,  # Horizontal padding (inside button)
            pady=25  # Vertical padding (inside button)
        )
        close_btn.pack(side='right', pady=0, padx=0)  # Added padx for spacing

        # Store references and setup effects
        self._widgets.update({'github_btn': github_btn, 'close_btn': close_btn})
        self._setup_button_effects()

    def _create_footer(self) -> None:
        """Create footer with credits"""
        tk.Label(
            self.dialog,
            text=Const.license,
            font=("Segoe UI", 8),
            fg=Const.colors['text_lighter'],
            bg=Const.colors['background']
        ).pack(side="bottom", pady=(0, 0), anchor='center')

    def _setup_button_effects(self) -> None:
        """Setup optimized button hover effects"""
        github_btn = self._widgets['github_btn']
        close_btn = self._widgets['close_btn']

        # GitHub button effects
        github_btn.bind("<Enter>", lambda e: self._set_button_color(github_btn, 'secondary', 'hover'))
        github_btn.bind("<Leave>", lambda e: self._set_button_color(github_btn, 'secondary', 'normal'))
        github_btn.bind("<Button-1>", lambda e: self._animate_button_click(github_btn, 'secondary'))

        # Close button effects
        close_btn.bind("<Enter>", lambda e: self._set_button_color(close_btn, 'primary', 'hover'))
        close_btn.bind("<Leave>", lambda e: self._set_button_color(close_btn, 'primary', 'normal'))
        close_btn.bind("<Button-1>", lambda e: self._animate_button_click(close_btn, 'primary', callback=self.close))

    def _set_button_color(self, button: tk.Button, color_type: str, state: str) -> None:
        """Set button color based on state"""
        if state == 'hover':
            color = self.HOVER_COLORS.get(color_type, Const.colors[color_type])
        elif state == 'active':
            color = self.ACTIVE_COLORS.get(color_type, Const.colors[color_type])
        else:
            color = Const.colors[color_type]

        button.config(bg=color)

    def _animate_button_click(self, button: tk.Button, color_type: str, callback=None) -> None:
        """Animate button click with callback"""
        self._set_button_color(button, color_type, 'active')
        delay = 150 if callback else 100
        self.dialog.after(delay, callback or (lambda: self._set_button_color(button, color_type, 'normal')))

    def _setup_events(self) -> None:
        """Setup keyboard and window events"""
        self.dialog.bind("<Escape>", lambda e: self.close())
        self.dialog.bind("<Return>", lambda e: self.close())
        self.dialog.protocol("WM_DELETE_WINDOW", self.close)
        self.dialog.focus_set()

    def _show_dialog(self) -> None:
        """Show dialog with fade-in animation"""
        self.dialog.attributes('-alpha', 0.0)
        self.dialog.lift()

        def fade_in(alpha: float = 0.0) -> None:
            alpha = min(1.0, alpha + 0.1)
            self.dialog.attributes('-alpha', alpha)
            if alpha < 1.0 and self.dialog and self.dialog.winfo_exists():
                self.dialog.after(20, lambda: fade_in(alpha))

        self.dialog.after(10, fade_in)

    @staticmethod
    def _open_url(url: str) -> None:
        """Open URL in default browser (avoids repeated imports)."""

        try:
            webbrowser.open(url, new=2)  # new=2 opens in new tab if possible

        except Exception:
            pass  # Silent fail (or add logging if needed

    def close(self) -> None:
        """Clean up and close the dialog"""
        if self.dialog and self.dialog.winfo_exists():
            self.dialog.grab_release()
            self.dialog.destroy()

        # Clear references
        self.dialog = None
        self._widgets.clear()


def main() -> None:
    """ This method will start the Application"""

    root = tk.Tk()

    PyCrafter(root)
    root.mainloop()


if __name__ == "__main__":
    main()