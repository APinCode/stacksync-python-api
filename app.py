from flask import Flask, request, jsonify
import os
import json
import subprocess
import uuid
import sys

app = Flask(__name__)

NSJAIL_CONFIG_PATH = "/etc/nsjail.cfg"
PYTHON_BIN = "/usr/local/bin/python3"
SANDBOX_ROOT = "/sandbox"
WRAPPER_PATH = "/app/executor.py"
RESULT_PREFIX = "___RESULT_JSON___:" 

def run_in_nsjail(script_path: str):
    """
    Run the given script inside nsjail using executor.py as a wrapper.

    Returns:
        stdout (str), stderr (str), exit_code (int)
    """
    cmd = [
        "nsjail",
        "--config", NSJAIL_CONFIG_PATH,
        "--",
        PYTHON_BIN,
        WRAPPER_PATH,
        script_path,
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stdout, stderr = proc.communicate()

    # If nsjail fails due to PR_SET_SECUREBITS / kernel restrictions (Cloud Run),
    # fall back to running the executor directly.
    if proc.returncode == 255 and "PR_SET_SECUREBITS" in stderr:
        print("nsjail unsupported in this environment, falling back to direct execution", file=sys.stderr)

        fallback_cmd = [
            PYTHON_BIN,
            WRAPPER_PATH,
            script_path,
        ]
        fallback_proc = subprocess.Popen(
            fallback_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        fb_stdout, fb_stderr = fallback_proc.communicate()
        return fb_stdout, fb_stderr, fallback_proc.returncode

    return stdout, stderr, proc.returncode

@app.route("/execute", methods=["POST"])
def execute():
    """
    Main execution endpoint.

    Expects JSON body:
        { "script": "<python code defining main()>" }

    Returns JSON:
        {
          "result": <main() return value as JSON>,
          "stdout": "<captured stdout>"
        }
    """
    # Input validation
    if not request.is_json:
        return jsonify({"error": "Request body must be JSON"}), 400
    
    # Parse Request body as JSON
    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"error": "Invalid JSON"}), 400
    
    # Validate Script
    script = body.get("script")
    if not isinstance(script, str) or not script.strip():
        return jsonify({"error": "`script` must be a non-empty string"}), 400

    # Save the script into a temporary file with a unique id to avoid collisions
    os.makedirs(SANDBOX_ROOT, exist_ok=True)
    script_id = str(uuid.uuid4())
    script_filename = f"user_script_{script_id}.py"
    script_path = os.path.join(SANDBOX_ROOT, script_filename)
    with open(script_path, "w") as f:
        f.write(script)

    # Execute the script via nsjail
    stdout, stderr, code = run_in_nsjail(script_path)

    # If the execution failed return an error
    if code != 0:
        return jsonify({
            "error": "Script execution failed",
            "exit_code": code,
            "stderr": stderr,
            "stdout": stdout,
        }), 400

    # Parse stdout lines:
    result_json_str = None
    user_stdout_lines = []
    for line in stdout.splitlines():
        if line.startswith(RESULT_PREFIX):
            # Retrieve the rest of the line after the prefix (We only retrieve the last one which shouldn't be an issue since we only output one)
            result_json_str = line[len(RESULT_PREFIX):]
        else:
            user_stdout_lines.append(line)

    # If the execution didn't return a result return an error
    if result_json_str is None:
        return jsonify({
            "error": "main() result not found. Ensure script defines main() and returns JSON.",
            "stderr": stderr,
            "stdout": stdout,
        }), 400

    # Try to parse the result into a JSON, if it fails return an error
    try:
        result = json.loads(result_json_str)
    except json.JSONDecodeError:
        return jsonify({
            "error": "main() did not return JSON-serializable object",
            "stderr": stderr,
            "stdout": stdout,
        }), 400

    # Return the result jsonified
    return jsonify({
        "result": result,
        "stdout": "\n".join(user_stdout_lines),
    })

# Simple endpoint to check that the service is up and running, for debugging
@app.route("/status", methods=["GET"])
def status():
    """Simple endpoint to check that the service is up."""
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
