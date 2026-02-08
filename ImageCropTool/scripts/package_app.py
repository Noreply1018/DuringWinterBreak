import subprocess
import os
import sys
import shutil

try:
    from PyInstaller.utils.hooks import collect_all
except ImportError:
    print("PyInstaller not found or version too old. Please install pyinstaller.")
    sys.exit(1)

def run_pyinstaller():
    # Define paths
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    entry_point = os.path.join(project_dir, "gui_main.py")
    dist_path = os.path.join(project_dir, "build")
    work_path = os.path.join(project_dir, "build", "temp")
    spec_path = os.path.join(project_dir, "build")
    icon_path = os.path.join(project_dir, "icon.ico")
    data_dir = os.path.join(project_dir, "data")
    
    # Ensure build directory exists
    os.makedirs(dist_path, exist_ok=True)

    # Collect osgeo dependencies
    try:
        datas, binaries, hiddenimports = collect_all('osgeo')
    except Exception as e:
        print(f"Warning: collect_all('osgeo') failed: {e}")
        datas, binaries, hiddenimports = [], [], []

    # Prepare additional arguments for PyInstaller
    add_data_args = []
    # Add project data
    if os.path.exists(data_dir):
        add_data_args.append(f"--add-data={data_dir}{os.pathsep}data")

    # Add osgeo data
    for src, dest in datas:
        add_data_args.append(f"--add-data={src}{os.pathsep}{dest}")
    
    add_binary_args = []
    for src, dest in binaries:
        add_binary_args.append(f"--add-binary={src}{os.pathsep}{dest}")

    hidden_import_args = []
    for hidden in hiddenimports:
        hidden_import_args.append(f"--hidden-import={hidden}")

    # Manually collect critical GDAL DLLs that collect_all misses
    conda_root = os.path.dirname(os.path.dirname(sys.executable)) # Assuming python is in env/ or env/Scripts? 
    # Actually sys.executable in conda env is usually Env/python.exe.
    # Library/bin is Env/Library/bin
    
    # Check if we are in a conda env structure
    library_bin = os.path.join(os.path.dirname(sys.executable), "Library", "bin")
    if not os.path.exists(library_bin):
        # Try one level up if python is in Scripts/
        library_bin = os.path.join(os.path.dirname(os.path.dirname(sys.executable)), "Library", "bin")

    if os.path.exists(library_bin):
        print(f"Found Conda Library/bin at: {library_bin}")
        dll_patterns = [
            "gdal*.dll",
            "geos*.dll",
            "proj*.dll",
            "sqlite3.dll",
            "libtiff.dll",
            "libpng16.dll",
            "libjpeg.dll",
            "libwebp.dll",
            "openjp2.dll",
            "netcdf.dll",
            "hdf5.dll"
        ]
        
        import glob
        for pattern in dll_patterns:
            search_path = os.path.join(library_bin, pattern)
            found_dlls = glob.glob(search_path)
            for dll in found_dlls:
                # Add to the root of the internal directory (.)
                print(f"Adding binary: {os.path.basename(dll)}")
                add_binary_args.append(f"--add-binary={dll}{os.pathsep}.")
    else:
        print("Warning: Could not locate Conda Library/bin to manually add DLLs.")

    # Base command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconsole",
        "--clean",
        "--name=ImageCropTool",
        f"--distpath={dist_path}",
        f"--workpath={work_path}",
        f"--specpath={spec_path}",
        entry_point
    ]
    
    cmd.extend(add_data_args)
    cmd.extend(add_binary_args)
    cmd.extend(hidden_import_args)
    
    # Add icon if exists
    if os.path.exists(icon_path):
        cmd.append(f"--icon={icon_path}")
        print(f"Using icon: {icon_path}")
    else:
        print("Warning: Icon file not found, using default icon.")
        
    print("Running PyInstaller with command:")
    # Print command clearly (handling spaces in paths might make it look weird if printed simply joined)
    print(" ".join([f'"{c}"' if " " in c else c for c in cmd]))
    
    try:
        subprocess.check_call(cmd)
        print("PyInstaller packaging completed successfully.")
        
        # Post-processing: Manually copy GDAL dependencies to _internal
        print("Starting post-packaging dependency copy...")
        dist_app_dir = os.path.join(dist_path, "ImageCropTool")
        internal_dir = os.path.join(dist_app_dir, "_internal")
        if not os.path.exists(internal_dir):
             internal_dir = dist_app_dir # Fallback for older PyInstaller or one-file extracted
        
        # Locate Conda Library/bin and share
        conda_env = os.path.dirname(sys.executable)
        library_bin = os.path.join(conda_env, "Library", "bin")
        library_share = os.path.join(conda_env, "Library", "share")
        
        if not os.path.exists(library_bin):
            conda_env = os.path.dirname(conda_env) # Try one level up
            library_bin = os.path.join(conda_env, "Library", "bin")
            library_share = os.path.join(conda_env, "Library", "share")
            
        if os.path.exists(library_bin):
            import glob
            dll_patterns = [
                "gdal*.dll", "geos*.dll", "proj*.dll", "sqlite3.dll",
                "libtiff.dll", "libpng16.dll", "libjpeg.dll", "libwebp.dll",
                "openjp2.dll", "netcdf.dll", "hdf5.dll"
            ]
            
            print(f"Copying DLLs from {library_bin} to {internal_dir}...")
            count = 0
            for pattern in dll_patterns:
                for dll in glob.glob(os.path.join(library_bin, pattern)):
                    dest = os.path.join(internal_dir, os.path.basename(dll))
                    if not os.path.exists(dest):
                        shutil.copy2(dll, dest)
                        count += 1
                        print(f"  Copied {os.path.basename(dll)}")
            print(f"Copied {count} DLLs.")
            
            # Copy data directories
            # GDAL_DATA
            gdal_data_src = os.path.join(library_share, "gdal")
            gdal_data_dest = os.path.join(internal_dir, "gdal-data")
            if os.path.exists(gdal_data_src):
                if os.path.exists(gdal_data_dest):
                    shutil.rmtree(gdal_data_dest)
                shutil.copytree(gdal_data_src, gdal_data_dest)
                print(f"Copied GDAL data to {gdal_data_dest}")
                
            # PROJ_LIB
            proj_data_src = os.path.join(library_share, "proj")
            proj_data_dest = os.path.join(internal_dir, "proj-data")
            if os.path.exists(proj_data_src):
                if os.path.exists(proj_data_dest):
                    shutil.rmtree(proj_data_dest)
                shutil.copytree(proj_data_src, proj_data_dest)
                print(f"Copied PROJ data to {proj_data_dest}")
        else:
            print("Warning: Could not locate Conda Library/bin for post-processing copy.")

    except subprocess.CalledProcessError as e:
        print(f"Packaging failed with error: {e}")
    except FileNotFoundError:
        print("PyInstaller not found. Please ensure it is installed in the current environment.")

if __name__ == "__main__":
    run_pyinstaller()
