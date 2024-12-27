import pickle
import numpy
# Properly open the pickle file in binary read mode
with open('embeddings.pkl', 'rb') as file:
    a = pickle.load(file)

# Print the loaded object
print(a)
