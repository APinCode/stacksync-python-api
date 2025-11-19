import runpy
import sys
import json

RESULT_PREFIX = "___RESULT_JSON___:"


def main():
    """
    Wrapper executed inside nsjail.

    - Loads the user script from the given path.
    - Retrieves and calls main().
    - Ensures the return value is JSON-serializable.
    - Prints a single RESULT_PREFIX + JSON line to stdout.
    """
    if len(sys.argv) != 2:
        print("Usage: executor.py <path_to_script>", file=sys.stderr)
        sys.exit(1)

    script_path = sys.argv[1]

    # Execute the user's script in its own global namespace
    try:
        script_globals = runpy.run_path(script_path)
    except Exception as e:
        print(f"Error while executing user script: {e}", file=sys.stderr)
        sys.exit(1)

    # Get the main() function
    user_main = script_globals.get("main")
    if not callable(user_main):
        print("Error: Script must define a callable main()", file=sys.stderr)
        sys.exit(1)

    # Call main()
    try:
        result = user_main()
    except Exception as e:
        print(f"Error while running main(): {e}", file=sys.stderr)
        sys.exit(1)

    # Ensure it's JSON-serializable
    try:
        json_str = json.dumps(result)
    except TypeError as e:
        print(f"Error: main() must return JSON-serializable object: {e}", file=sys.stderr)
        sys.exit(1)

    # Print the result with the defined prefix to parse it in the endpoint
    print(f"{RESULT_PREFIX}{json_str}")


if __name__ == "__main__":
    main()
