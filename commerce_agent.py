import os
import json
import argparse
import asyncio
import re
import sys
from typing import Optional
from dotenv import load_dotenv
import asyncio.subprocess
from droidrun.agent.droid.droid_agent import DroidAgent
from droidrun import AdbTools

load_dotenv()

class CommerceAgent:
    def __init__(self, provider="gemini", model="gemini-1.5-flash"):
        self.provider = provider
        self.model = model
        self._ensure_api_keys()

    def _ensure_api_keys(self):
        keys = ["GEMINI_API_KEY", "GOOGLE_API_KEY"]
        if self.provider == "gemini" and not any(os.getenv(k) for k in keys):
             print("[Warn] GEMINI_API_KEY not found in env, checking GOOGLE_API_KEY")

    def _parse_price(self, price_str):
        if not price_str: 
            return float('inf')
        try:
            val_str = str(price_str).lower()
            filtered = ''.join([c for c in val_str if c.isdigit() or c == '.'])
            if not filtered:
                return float('inf')
            return float(filtered)
        except Exception:
            return float('inf')

    async def execute_task(self, app_name: str, query: Optional[str] = None, item_type: str = "product", action: str = "search", target_item: Optional[str] = None, url: Optional[str] = None) -> dict:
        print(f"\n[CommerceAgent] Initializing Task for: {app_name} (Action: {action})")
        
        goal_templates = {
            "url": (
                f"Open the app '{app_name}'. Navigate directly to the URL: '{url}'. "
                f"Wait for loading. Visually SCAN the page. "
                f"Extract: 1. Product Name (title), 2. Price (numeric), 3. Rating, 4. Restaurant/Seller Name. "
                f"Return JSON with keys: 'title', 'price', 'rating', 'restaurant'. "
                f"If unavailable, return status='failed'."
            ),
            "order": (
                f"Open '{app_name}'. Search for '{query}'. Wait for results. "
                f"Visually SCAN and select the item '{target_item}' or the first relevant one. "
                f"Add to Cart. Go to View Cart. Proceed to Pay/Checkout. "
                f"Select 'Cash on Delivery' or 'Pay on Delivery'. "
                f"CRITICAL: Finalize the order by clicking 'Place Order' or 'Confirm'. "
                f"Return JSON keys: 'status' (success/failed), 'order_id', 'final_price'."
            ),
            "search": (
                f"Open '{app_name}'. Search for '{query}'. Wait for load. "
                f"Visually SCAN results. Identify multiple items matching '{query}'. "
                f"COMPARE prices. Select the CHEAPEST option. "
                f"Extract: 1. Title, 2. Price, 3. Rating, 4. Restaurant. "
                f"Return JSON keys: 'title', 'price', 'rating', 'restaurant'. "
                f"Find closest match if no exact match."
            )
        }

        if url:
            goal = goal_templates["url"]
        elif action == "order":
            goal = goal_templates["order"]
        else:
            goal = goal_templates["search"]

        from droidrun.agent.utils.llm_picker import load_llm

        key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        llm = load_llm(
            provider_name="GoogleGenAI",
            model=self.model,
            api_key=key
        )

        try:
             from droidrun.config_manager import DroidrunConfig, AgentConfig, ManagerConfig, ExecutorConfig, TelemetryConfig
             config = DroidrunConfig(
                 agent=AgentConfig(
                     reasoning=False, 
                     manager=ManagerConfig(vision=True), 
                     executor=ExecutorConfig(vision=True)
                 ), 
                 telemetry=TelemetryConfig(enabled=False)
             )
             agent = DroidAgent(goal=goal, llms=llm, config=config)
        except ImportError:
             agent = DroidAgent(goal=goal, llm=llm, vision=True, reasoning=False)

        output_payload = {"platform": app_name, "status": "failed", "data": {}}
        
        try:
            print(f"[CommerceAgent] 🧠 Running Agent Logic...")
            raw_result = await agent.run()
            
            if raw_result:
                text_res = str(getattr(raw_result, 'reason', raw_result)).strip()
                
                if "<request_accomplished" in text_res:
                    parts = text_res.split(">")
                    if len(parts) > 1:
                        text_res = parts[1].split("</request_accomplished>")[0].strip()
                
                if "```" in text_res:
                    content = text_res.split("```")
                    text_res = content[1] if len(content) > 1 else text_res
                    if text_res.startswith("json"):
                        text_res = text_res[4:].strip()
                
                text_res = text_res.strip()
                
                if text_res.startswith("{"):
                    try:
                         parsed = json.loads(text_res)
                         output_payload["data"] = parsed
                         output_payload["status"] = "success"
                         output_payload["data"]["numeric_price"] = self._parse_price(parsed.get("price"))
                         output_payload["data"].setdefault("restaurant", "Unknown")
                    except json.JSONDecodeError:
                         pass
            
            return output_payload

        except Exception as e:
            return output_payload

    async def auto_order_cheapest(self, query):
        print(f"\n[CommerceAgent] 🤖 Autonomous Ordering Sequence Initiated for: '{query}'")
        
        platforms = ["Zomato", "Swiggy"]
        search_results = {}
        
        for p in platforms:
            search_results[p.lower()] = await self.execute_task(p, query, "food item", action="search")
            await asyncio.sleep(2)

        valid_results = [
            (p, res) for p, res in search_results.items() 
            if res.get('status') == 'success' and res['data'].get('numeric_price', float('inf')) != float('inf')
        ]
        
        if not valid_results:
             print("\n❌ Could not determine valid pricing. Aborting.")
             return search_results

        best_platform, best_res = min(valid_results, key=lambda x: x[1]['data']['numeric_price'])
        
        target_app = "Zomato" if best_platform == "zomato" else "Swiggy"
        target_title = best_res['data'].get('title')
        best_price = best_res['data'].get('price')

        print(f"\n[CommerceAgent] 🏆 Best Deal identify: {target_app} @ {best_price}")
        print(f"Details: {target_title}")
        print(f"Proceeding to ORDER on {target_app}...")
        
        booking_out = await self.execute_task(target_app, query, "food item", action="order", target_item=target_title)
        
        search_results["order_status"] = booking_out
        return search_results

async def main():
    parser = argparse.ArgumentParser(description="BestBuy-Agent: Commerce Automation (DroidRun)")
    parser.add_argument("--task", choices=['shopping', 'food'], default='shopping')
    parser.add_argument("--query", required=True)
    parser.add_argument("--action", choices=['search', 'order'], default='search', help="Action to perform")
    parser.add_argument("--app", help="App name")
    args = parser.parse_args()

    bot = CommerceAgent(provider="gemini", model="models/gemini-2.5-flash")
    
    if args.action == "order" and not args.app:
        await bot.auto_order_cheapest(args.query)
    else:
        target_platforms = ["Zomato", "Swiggy"] if args.task == "food" else ["Amazon", "Flipkart"]
        
        if args.app:
            target_platforms = [p for p in target_platforms if p.lower() == args.app.lower()]

        final_res = {}
        for p in target_platforms:
            res = await bot.execute_task(p, args.query, "product" if args.task == "shopping" else "food item", action=args.action)
            final_res[p.lower()] = res
            await asyncio.sleep(2)
            
        print("\n--- Final Results ---")
        print(json.dumps(final_res, indent=2))

if __name__ == "__main__":
    asyncio.run(main())