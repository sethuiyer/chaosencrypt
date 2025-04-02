import numpy as np

# Set seed for reproducibility
np.random.seed(42)

# Generate 100 million random floats in [0,1)
n = 100_000_000
random_floats = np.random.rand(n)

# Multiply by 9973 and take mod 1
chaos_values = (random_floats * 9973) % 1

# Convert to 8-bit integers (scale to 0-255)
chaos_bytes = (chaos_values * 256).astype(np.uint8)

# Save to binary file
bin_file_path = "chaos_9973_mod1_100M.bin"
chaos_bytes.tofile(bin_file_path)

bin_file_path

