import os

library_path = os.path.join(os.path.dirname(__file__), 'turing-smart-screen-python-main', 'library')
print(f"Library path: {library_path}")
print(f"Library exists: {os.path.exists(library_path)}")

if os.path.exists(library_path):
    print("Contents of library folder:")
    for item in os.listdir(library_path):
        print(f"  {item}")
        if item == 'turing_smart_screen_python':
            subpath = os.path.join(library_path, item)
            print(f"    Contents of {item}:")
            for subitem in os.listdir(subpath):
                print(f"      {subitem}")