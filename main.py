import os

def create_tree_of_project(directory_name):
    path = f'data/{directory_name}'
    all_paths = []
    print(os.walk(path))
    for root, dirs, files in os.walk(path):
        for dir_name in dirs:
            all_paths.append(os.path.join(root, dir_name))
        for file_name in files:
            all_paths.append(os.path.join(root, file_name))

    return all_paths



directory_path = 'Optics-Hackathon'
all_paths = create_tree_of_project(directory_path)

for path in all_paths:
    print(path)
