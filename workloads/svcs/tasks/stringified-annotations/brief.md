# Handle string annotations when detecting the container parameter

A factory may declare that it wants the container by annotating its first
parameter as `svcs.Container`. Detecting that means inspecting the annotation.

Annotations are not always objects. Under `from __future__ import annotations`,
and wherever a forward reference is written, the annotation arrives as a string.
The current detection mishandles those, so a factory whose container parameter
is annotated as a string is not recognised as wanting the container.

Make the detection treat string annotations equivalently to their resolved
counterparts, so a factory is recognised the same way whether its annotation was
evaluated or left as a string.

Factories that do not take a container must continue not to receive one.
