import sys
import os

# Remove the current directory from sys.path to prevent NLTK's security check from false triggering
current_dir = os.path.abspath(os.getcwd())
sys.path = [p for p in sys.path if p and os.path.abspath(p) != current_dir]

import nltk
nltk.download('wordnet')
nltk.download('omw-1.4')
print("NLTK Data downloaded successfully!")
