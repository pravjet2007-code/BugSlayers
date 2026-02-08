import os
import json
import argparse
import asyncio
import re
import sys
from dotenv import load_dotenv

from droidrun.agent.droid.droid_agent import DroidAgent
from droidrun.agent.utils.llm_picker import load_llm
from droidrun import AdbTools

load_dotenv()

class RideComparisonAgent:
    def __init__(self, provider="gemini", model="gemini-1.5-flash"):
        self.provider = provider
        self.model = model
        self._ensure_api_keys()

    def _ensure_api_keys(self):
        possible_keys = ["GEMINI_API_KEY", "GOOGLE_API_KEY"]
        has_key = any(os.environ.get(k) for k in possible_keys)
        if self.provider == "gemini" and not has_key:
             print("[Warn] GEMINI_API_KEY not found in env, checking GOOGLE_API_KEY")

    def _parse_price(self, price_str):
        if not price_str:
            return float('inf')
        try:
            s = str(price_str).lower()
            allowed = "0123456789."
            digits_only = "".join([c for c in s if c in allowed])
            return float(digits_only) if digits_only else float('inf')
        except:
            return float('inf')

    async def execute_task(self, app_name: str, pickup: str, drop: str, preference: str = "cab", action: str = "compare") -> dict:
        print(f"\n[RideAgent] Initializing Task for: {app_name} (Action: {action}, Pref: {preference})")
        
        kw_map = {
            "uber": {"auto": "Uber Auto", "sedan": "Uber Premier", "cab": "Uber Go, Uber Moto"},
            "ola": {"auto": "Ola Auto", "sedan": "Ola Prime Sedan", "cab": "Ola Mini, Ola Bike"}
        }
        
        app_key = app_name.lower()
        ride_keywords = kw_map.get(app_key, {}).get(preference, "Standard Ride")

        goals = {
            "book": (
                f"Open '{app_name}'. Handle permissions if needed ('Allow'). "
                f"Click 'Ride'/Search. Input Pickup: '{pickup}'. Input Drop: '{drop}'. "
                f"Wait for options. Select CHEAPEST ride matching '{preference}' (Keywords: {ride_keywords}). "
                f"Click Book/Confirm. Ensure Payment is 'Cash'. Confirm Booking. "
                f"Wait for Driver Screen. Extract: Driver Name, Vehicle No, OTP. "
                f"Return JSON: 'status', 'driver_details', 'cab_details', 'price', 'eta'."
            ),
            "compare": (
                f"Open '{app_name}'. Handle permissions. "
                f"Click 'Ride'/Search. Input Pickup: '{pickup}'. Input Drop: '{drop}'. "
                f"Wait for list. SCAN for rides matching '{preference}' (Keywords: {ride_keywords}). "
                f"Extract ride type, price, and ETA. "
                f"Return JSON: 'app', 'ride_type', 'price', 'eta'. Strict JSON."
            )
        }
        
        goal = goals.get(action, goals["compare"])

        key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        p_name = "GoogleGenAI" if self.provider == "gemini" else self.provider

        llm = load_llm(provider_name=p_name, model=self.model, api_key=key)

        try:
             from droidrun.config_manager import DroidrunConfig, AgentConfig, ManagerConfig, ExecutorConfig, TelemetryConfig
             cfg = DroidrunConfig(
                 agent=AgentConfig(
                     reasoning=False, 
                     manager=ManagerConfig(vision=True), 
                     executor=ExecutorConfig(vision=True)
                 ), 
                 telemetry=TelemetryConfig(enabled=False)
             )
             agent = DroidAgent(goal=goal, llms=llm, config=cfg)
        except ImportError:
             agent = DroidAgent(goal=goal, llm=llm, vision=True, reasoning=False)

        res_payload = {"app": app_name, "status": "failed", "data": {}, "numeric_price": float('inf')}

        try:
            print(f"[RideAgent] 🧠 Running Agent on {app_name}...")
            resp = await agent.run()
            
            if resp:
                raw_json = str(getattr(resp, 'reason', resp)).strip()

                if "<request_accomplished" in raw_json:
                    parts = raw_json.split(">")
                    if len(parts) > 1:
                        raw_json = parts[1].split("</request_accomplished>")[0].strip()
                
                if "```" in raw_json:
                    blocks = raw_json.split("```")
                    raw_json = blocks[1] if len(blocks) > 1 else raw_json
                    if raw_json.startswith("json"):
                         raw_json = raw_json[4:].strip()

                raw_json = raw_json.strip()
                
                if raw_json.startswith("{"):
                    try:
                        parsed = json.loads(raw_json)
                        res_payload["data"] = parsed
                        res_payload["status"] = "success"
                        res_payload["numeric_price"] = self._parse_price(parsed.get("price"))
                    except json.JSONDecodeError:
                        pass
            
            return res_payload

        except Exception as e:
            print(f"[Error] Execution Failed: {e}")
            return res_payload

    async def compare_rides(self, pickup, drop, preference="cab"):
        targets = ["Uber", "Ola"]
        agg_results = {}

        for t in targets:
            agg_results[t] = await self.execute_task(t, pickup, drop, preference, action="compare")
            await asyncio.sleep(3)

        print("\n--- Final Aggregated Results ---")
        
        valid_options = []
        for name, r in agg_results.items():
            if r["status"] == "success":
                p_val = r["numeric_price"]
                print(f"{name}: {r['data'].get('ride_type')} - {r['data'].get('price')} (Num: {p_val})")
                valid_options.append(r)
            else:
                print(f"{name}: No Data")

        best_choice = None
        if valid_options:
            best_choice = min(valid_options, key=lambda x: x["numeric_price"])
            agg_results["best_deal"] = best_choice
            print(f"\n🏆 Best Deal: {best_choice['app']} - {best_choice['data'].get('price')}")
        else:
            print("\n❌ Could not determine best deal.")
        
        return agg_results

    async def book_cheapest_ride(self, pickup, drop, preference="cab"):
        print(f"\n[RideAgent] 🤖 Autonomous Booking Sequence Initiated...")
        
        comp_res = await self.compare_rides(pickup, drop, preference)
        winner = comp_res.get("best_deal")
        
        if not winner:
            return {"status": "failed", "message": "No rides found"}
        
        app_target = winner['app']
        cost = winner['data'].get('price')
        print(f"[RideAgent] 🏆 Proceeding to BOOK on {app_target} @ {cost}...")
        
        book_res = await self.execute_task(app_target, pickup, drop, preference, action="book")
        
        stat = book_res.get('status')
        print(f"\n[RideAgent] Booking Status: {stat}")
        
        if stat == 'success':
             print(f"✅ Cab Booked! Driver: {book_res['data'].get('driver_details')}")
        else:
             print("❌ Booking Failed.")

        return book_res

async def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pickup", required=True)
    p.add_argument("--drop", required=True)
    p.add_argument("--preference", default="cab", choices=["cab", "auto", "sedan"])
    p.add_argument("--action", default="compare", choices=["compare", "book"])
    args = p.parse_args()

    agent_inst = RideComparisonAgent(model="models/gemini-2.5-flash")
    
    if args.action == "book":
        await agent_inst.book_cheapest_ride(args.pickup, args.drop, args.preference)
    else:
        await agent_inst.compare_rides(args.pickup, args.drop, args.preference)

if __name__ == "__main__":
    asyncio.run(main())
