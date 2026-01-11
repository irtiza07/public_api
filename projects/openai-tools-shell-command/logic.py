"""
OpenAI Shell Tool Tutorial

This demonstrates using OpenAI's built-in Shell tool (GPT-5.1+) to execute
shell commands on your local computer through the Responses API.

⚠️ WARNING: This executes arbitrary shell commands without sandboxing.
   Only for demonstration purposes. In production, use proper sandboxing!
"""

import os
import subprocess
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from openai import OpenAI
from dotenv import load_dotenv

# Load environment and OpenAI client
load_dotenv()
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable not set.")
client = OpenAI(api_key=api_key)


@dataclass
class CommandResult:
    """Result of a shell command execution."""

    stdout: str
    stderr: str
    exit_code: Optional[int]
    timed_out: bool


class ShellExecutor:
    """Executes shell commands with timeout support."""

    def __init__(self, default_timeout: float = 60):
        self.default_timeout = default_timeout

    def run(self, cmd: str, timeout: Optional[float] = None) -> CommandResult:
        """
        Execute a shell command and return the result.

        Args:
            cmd: Shell command to execute
            timeout: Timeout in seconds (uses default if None)

        Returns:
            CommandResult with stdout, stderr, exit_code, and timeout status
        """
        t = timeout or self.default_timeout

        print(f"      🔧 Executing: {cmd}")

        p = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            out, err = p.communicate(timeout=t)
            return CommandResult(out, err, p.returncode, False)
        except subprocess.TimeoutExpired:
            p.kill()
            out, err = p.communicate()
            return CommandResult(out, err, p.returncode, True)


def ask_permission(commands: List[str]) -> bool:
    """
    Ask user for permission to execute shell commands.

    Args:
        commands: List of shell commands to execute

    Returns:
        True if user approves, False otherwise
    """
    print(f"\n⚠️  About to execute {len(commands)} command(s):")
    for i, cmd in enumerate(commands, 1):
        print(f"   {i}. {cmd}")

    while True:
        response = input("\n🔐 Execute these commands? (y/n): ").strip().lower()
        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
        else:
            print("   Please enter 'y' or 'n'")


def handle_user_query(
    user_query: str, previous_response_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Handle a user query using OpenAI's built-in Shell tool.

    Args:
        user_query: The user's question or request
        previous_response_id: ID of the previous response to continue the conversation

    Returns:
        Dictionary with results and shell execution details
    """

    print(f"\n🔍 User Query: {user_query}")

    executor = ShellExecutor(default_timeout=60)

    try:
        # Call Responses API with the Shell tool
        response = client.responses.create(
            model="gpt-5.1",
            input=user_query,
            previous_response_id=previous_response_id,
            instructions="The local bash shell environment is on Mac. Be concise and clear in your responses.",
            tools=[{"type": "shell"}],
        )

        # Check if the model wants to execute shell commands
        shell_calls = [
            item
            for item in response.output
            if hasattr(item, "type") and item.type == "shell_call"
        ]

        if shell_calls:
            print(f"\n📊 Found {len(shell_calls)} shell_call(s)")

            # Process all shell calls
            shell_outputs = []

            for shell_call in shell_calls:
                call_id = shell_call.call_id
                action = shell_call.action
                commands = action.commands
                timeout_ms = getattr(action, "timeout_ms", None)
                max_output_length = getattr(action, "max_output_length", None)

                print(f"\n   🔨 Shell Call ID: {call_id}")
                print(f"   📝 Commands: {commands}")
                print(
                    f"   ⏱️  Timeout: {timeout_ms}ms"
                    if timeout_ms
                    else "   ⏱️  Timeout: default"
                )

                # Ask for user permission
                if not ask_permission(commands):
                    print(f"   ❌ User denied execution")
                    # Send back an error message to the model
                    command_results = [
                        {
                            "stdout": "",
                            "stderr": "User denied permission to execute this command.",
                            "outcome": {"type": "exit", "exit_code": 1},
                        }
                        for _ in commands
                    ]

                    shell_output = {
                        "type": "shell_call_output",
                        "call_id": call_id,
                        "output": command_results,
                    }
                    if max_output_length is not None:
                        shell_output["max_output_length"] = max_output_length
                    shell_outputs.append(shell_output)
                    continue

                # Execute all commands (can be concurrent, but doing sequentially for simplicity)
                command_results = []
                for cmd in commands:
                    timeout_sec = (timeout_ms / 1000.0) if timeout_ms else None
                    result = executor.run(cmd, timeout_sec)

                    # Build outcome
                    if result.timed_out:
                        outcome = {"type": "timeout"}
                    else:
                        outcome = {"type": "exit", "exit_code": result.exit_code}

                    command_results.append(
                        {
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                            "outcome": outcome,
                        }
                    )

                    print(
                        f"      ✅ Exit: {result.exit_code}, Timed out: {result.timed_out}"
                    )
                    if result.stdout:
                        print(f"      📤 stdout: {result.stdout[:200]}...")
                    if result.stderr:
                        print(f"      ⚠️  stderr: {result.stderr[:200]}...")

                # Build shell_call_output
                shell_output = {
                    "type": "shell_call_output",
                    "call_id": call_id,
                    "output": command_results,
                }

                # Include max_output_length if it was provided
                if max_output_length is not None:
                    shell_output["max_output_length"] = max_output_length

                shell_outputs.append(shell_output)

            # Send all shell outputs back to the model
            print(f"\n📤 Sending {len(shell_outputs)} shell output(s) back to model...")

            followup = client.responses.create(
                model="gpt-5.1",
                previous_response_id=response.id,
                input=shell_outputs,
                tools=[{"type": "shell"}],
            )

            return {"status": "success", "response": followup}

        # No shell calls, just return the response
        return {"status": "success", "response": response}

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return {"status": "error", "error": str(e)}


def interactive_mode():
    """Interactive mode for testing OpenAI's Shell tool."""
    print("=" * 70)
    print("🚀 OpenAI Shell Tool Tutorial (GPT-5.1)")
    print("=" * 70)
    print("\n⚠️  WARNING: Executing shell commands without sandboxing!")
    print("   Only for demonstration. Use proper sandboxing in production.\n")
    print("💡 Try these queries:")
    print("  • 'What's my IP address?'")
    print("  • 'What version of Python and Node do I have?'")
    print("  • 'Show me running processes'")
    print("  • 'Find the largest file in the current directory'")
    print("  • 'What's my current directory?'")
    print("\nType 'quit' to exit\n")

    previous_response_id = None

    while True:
        user_input = input("💭 Your query: ").strip()

        if user_input.lower() in ["quit", "exit", "q"]:
            print("\n👋 Goodbye!")
            break
        elif not user_input:
            continue

        final_result = handle_user_query(user_input, previous_response_id)

        if final_result.get("status") == "success":
            # Print final answer
            print("\n" + "=" * 70)
            print("💬 ASSISTANT:")
            print("=" * 70)
            response_text = final_result["response"].output[0].content[0].text
            print(response_text)
            previous_response_id = final_result["response"].id
        else:
            print(f"\n❌ Error: {final_result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    interactive_mode()
