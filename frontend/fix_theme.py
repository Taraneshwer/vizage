import os
import re

def replace_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

                                              
    replacements = {
        r'text-white': 'text-gray-900',
        r'text-gray-100': 'text-gray-800',
        r'text-gray-300': 'text-gray-700',
        r'text-gray-400': 'text-gray-600',
        r'text-gray-500': 'text-gray-500',
        r'bg-white/5': 'bg-gray-100',
        r'bg-white/10': 'bg-gray-200',
        r'border-white/5': 'border-gray-200',
        r'border-white/10': 'border-gray-300',
        r'hover:text-white': 'hover:text-gray-900',
        r'hover:bg-white/5': 'hover:bg-gray-100',
        r'hover:bg-white/10': 'hover:bg-gray-200',
    }

    new_content = content
    for pattern, repl in replacements.items():
                                                                                                          
        new_content = re.sub(rf'\b{pattern}\b', repl, new_content)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

def process_directory(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(('.tsx', '.ts', '.jsx', '.js', '.html')):
                filepath = os.path.join(root, file)
                replace_in_file(filepath)

if __name__ == '__main__':
    src_dir = os.path.join(os.path.dirname(__file__), 'src')
    process_directory(src_dir)
