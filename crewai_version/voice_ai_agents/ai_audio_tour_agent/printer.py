"""
Simple printer utility for status updates.
Note: This is a simplified version compatible with Gradio interface.
"""

class Printer:
    """
    Simple wrapper to print status updates.
    """

    def __init__(self) -> None:
        self.items = {}

    def update_item(
        self, item_id: str, content: str, is_done: bool = False, hide_checkmark: bool = False
    ) -> None:
        prefix = "✅ " if is_done and not hide_checkmark else "🔄 "
        print(f"{prefix}{content}")
        self.items[item_id] = (content, is_done)

    def mark_item_done(self, item_id: str) -> None:
        if item_id in self.items:
            content = self.items[item_id][0]
            print(f"✅ {content}")
            self.items[item_id] = (content, True)

    def end(self) -> None:
        print("✅ All tasks completed!")
