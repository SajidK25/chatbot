from src.services.search_service import search_service


class ChatHandler:
    def __init__(self):
        self.search_service = search_service

    async def handle_message(self, message: str, platform: str = "telegram") -> str:
        parsed = self.search_service.parse_natural_language(message)
        products = await self.search_service.search_products(
            query=parsed["query"],
            max_price=parsed.get("max_price"),
            category=parsed.get("category"),
            gender=parsed.get("gender"),
            limit=3,
        )
        if not products:
            return self._no_results_message(parsed["query"])
        return self._format_products_message(products, platform)

    def _format_products_message(self, products: list[dict], platform: str) -> str:
        if platform == "whatsapp":
            return self._format_whatsapp_message(products)
        return self._format_telegram_message(products)

    def _format_telegram_message(self, products: list[dict]) -> str:
        lines = ["🛍️ *Here are my top recommendations:*\n"]
        for i, p in enumerate(products, 1):
            lines.append(f"{i}. *{p['name']}*")
            lines.append(f"   💰 ${p['price']:.2f}")
            lines.append(f"   📦 {p['brand']}")
            lines.append(f"   🔗 [Shop Now]({p['product_url']})")
            lines.append("")
        lines.append("👆 Tap to buy any of these!")
        return "\n".join(lines)

    def _format_whatsapp_message(self, products: list[dict]) -> str:
        lines = ["🛍️ Here are my top recommendations:\n"]
        for i, p in enumerate(products, 1):
            lines.append(f"{i}. {p['name']}")
            lines.append(f"   💰 ${p['price']:.2f} | {p['brand']}")
            lines.append(f"   🔗 {p['product_url']}")
            lines.append("")
        return "\n".join(lines)

    def _no_results_message(self, query: str) -> str:
        return (
            "😕 I couldn't find any products matching your search.\n\n"
            "Try phrases like:\n"
            '• "men\'s shoes under $100"\n'
            '• "wireless headphones under $50"\n'
            '�� "best running shoes for women"\n\n'
            "Or just describe what you're looking for!"
        )


chat_handler = ChatHandler()
