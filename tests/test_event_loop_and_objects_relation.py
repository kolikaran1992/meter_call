"""
========================================================================================
Event Loop & Object Binding Rule:
--------------------------------
An asynchronous object or resource (like a database connection pool) is bound to the
specific event loop on which it was created.

CORE RULE: All `async` operations on a resource (creation, usage, and cleanup) MUST
be performed on the same single, consistent event loop throughout its lifecycle.

Violation of this rule (e.g., using an object on a different or closed loop) will
result in a RuntimeError, often showing 'Event loop is closed'.
========================================================================================
"""

import asyncio


class LoopBoundObject:
    def __init__(self):
        # Store a reference to the event loop this object was created on
        try:
            self.creation_loop = asyncio.get_running_loop()
            print(f"Object created on loop: {id(self.creation_loop)}")
        except RuntimeError:
            print("Object created outside of a running event loop.")
            self.creation_loop = None

    async def run_on_correct_loop(self):
        # Check if the current loop is the same as the creation loop
        current_loop = asyncio.get_running_loop()
        print(f"Attempting to run on loop: {id(current_loop)}")
        if self.creation_loop is current_loop:
            print("Success! Running on the correct event loop.")
            await asyncio.sleep(0)
        else:
            raise RuntimeError(
                "Error: This object cannot be run on a different event loop!"
            )


# --- Scenario 1: Correct Usage (Success) ---
print("--- SCENARIO 1: Correct Usage ---")


async def main_success():
    my_object = LoopBoundObject()  # Object created on the main loop
    await my_object.run_on_correct_loop()


asyncio.run(main_success())
print("---------------------------------")
print("\n")


# --- Scenario 2: Incorrect Usage (RuntimeError) ---
print("--- SCENARIO 2: Incorrect Usage (RuntimeError) ---")


async def create_and_return_object():
    """Creates the object and returns it."""
    my_object = LoopBoundObject()
    # It's good practice to run any initial async setup here as well
    await my_object.run_on_correct_loop()
    return my_object


try:
    # First, run the creation coroutine on its own temporary loop
    temp_loop_object = asyncio.run(create_and_return_object())

    # Now, try to use the object on a different, second loop
    print("Attempting to use the object on a second, separate loop...")
    asyncio.run(temp_loop_object.run_on_correct_loop())

except RuntimeError as e:
    print(f"Caught expected RuntimeError: {e}")

print("---------------------------------")
