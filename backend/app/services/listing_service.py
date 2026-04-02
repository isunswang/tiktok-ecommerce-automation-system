"""Listing service - business logic for TikTok Shop listing."""

class ListingService:
    """Listing business logic layer."""

    @staticmethod
    async def match_category(product_name: str, description: str) -> dict:
        """Match TikTok Shop category for a product."""
        # TODO: Implement actual TikTok category matching
        return {
            "candidates": [
                {"category_id": "cat_001", "name": "Electronics", "confidence": 0.85},
                {"category_id": "cat_002", "name": "Accessories", "confidence": 0.72},
                {"category_id": "cat_003", "name": "Gadgets", "confidence": 0.60},
            ]
        }

    @staticmethod
    async def list_product(product_id: str, target_site: str, category_id: str) -> dict:
        """List product on TikTok Shop."""
        # TODO: Implement actual TikTok Shop listing API call
        return {
            "tiktok_product_id": f"TK_{product_id[:8]}",
            "status": "active",
            "message": "Product listed successfully",
        }
