import sys
from source_relocation.cli import main


if __name__ == "__main__":
    main(["internal", "--experiment", "code_control", *sys.argv[1:]])
