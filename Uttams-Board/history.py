"""Simple bounded undo/redo history using JSON snapshots."""

import json


class History:
    def __init__(self, limit=60):
        self.limit = limit
        self.stack = []
        self.index = -1

    def reset(self):
        self.stack = []
        self.index = -1

    def push(self, state):
        self.stack = self.stack[: self.index + 1]
        self.stack.append(json.dumps(state))
        if len(self.stack) > self.limit:
            self.stack.pop(0)
        self.index = len(self.stack) - 1

    def can_undo(self):
        return self.index > 0

    def can_redo(self):
        return self.index < len(self.stack) - 1

    def undo(self):
        if self.can_undo():
            self.index -= 1
            return json.loads(self.stack[self.index])
        return None

    def redo(self):
        if self.can_redo():
            self.index += 1
            return json.loads(self.stack[self.index])
        return None
