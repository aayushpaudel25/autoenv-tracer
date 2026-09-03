import sys
import runpy
from tracer import start_tracing, get_dependencies

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 src/main.py <path_to_script.py>")
        sys.exit(1)

    target_script = sys.argv[1]
    
    print(f"--- Starting trace for: {target_script} ---\n")
    
    start_tracing()
    
    try:
        runpy.run_path(target_script, run_name="__main__")
    except Exception as e:
        print(f"\n[ERROR] Target script crashed: {e}")
        
    print(f"\n--- Trace complete ---")
    
    # --- GENERATION PHASE ---
    print("\n--- Generating Environment ---")
    deps = get_dependencies()
    
    # 1. Write the requirements.txt file
    with open("generated_requirements.txt", "w") as f:
        for dep in deps:
            f.write(f"{dep}\n")
    print("[+] Created generated_requirements.txt")
    
    # 2. Write the Dockerfile
    dockerfile_content = f"""FROM python:3.11-slim
WORKDIR /app

# Copy and install the detected dependencies
COPY generated_requirements.txt .
RUN pip install -r generated_requirements.txt

# Copy the rest of the application
COPY . .

# Run the target script
CMD ["python", "{target_script}"]
"""
    
    with open("Dockerfile.autoenv", "w") as f:
        f.write(dockerfile_content)
    print("[+] Created Dockerfile.autoenv")

if __name__ == "__main__":
    main()