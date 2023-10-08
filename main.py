import sys
from iccad_prod_workflow_doc import perform_workflow

def main():
    if len(sys.argv) < 3:
        print("Usage: python main.py <noisemodel_name> <seed> [shots]")
        sys.exit(1)

    noisemodel_name = sys.argv[1]
    
    try:
        seed = int(sys.argv[2])
    except ValueError:
        print("Please provide a valid integer for <seed>")
        sys.exit(1)

    shots = 2852
    if len(sys.argv) == 4:
        try:
            shots = int(sys.argv[3])
        except ValueError:
            print("Please provide a valid integer for [shots]")
            sys.exit(1)

    perform_workflow(noisemodel_name, seed, shots)

if __name__ == "__main__":
    main()