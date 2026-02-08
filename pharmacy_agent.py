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

class PharmacyAgent:
    def __init__(self, provider="gemini", model="models/gemini-2.5-flash"):
        self.provider = provider
        self.model = model
        self._ensure_api_keys()

    def _ensure_api_keys(self):
        found = False
        for k in ["GEMINI_API_KEY", "GOOGLE_API_KEY"]:
            if os.getenv(k):
                found = True
                break
        if self.provider == "gemini" and not found:
             print("[Warn] GEMINI_API_KEY not found in env, checking GOOGLE_API_KEY")

    def _parse_price(self, price_str):
        if not price_str: return float('inf')
        try:
            return float("".join(filter(lambda x: x.isdigit() or x == '.', str(price_str))))
        except ValueError:
            return float('inf')

    async def execute_task(self, app_name: str, medicine: str, role: str) -> dict:
        print(f"\n[PharmaAgent] Initializing Task for: {app_name} - {medicine} ({role} mode)")
        
        is_pharmacist = (role == "pharmacist")
        
        instr_search = (
            f"Search for '{medicine}'. Look for bulk/wholesale packs or largest strips."
            if is_pharmacist else
            f"Search for '{medicine}'. Identify exact match for name and dosage."
        )
        
        goal = (
            f"Open '{app_name}'. Handle permissions. "
            f"Click Search. {instr_search} "
            f"Visually identify best result. Extract Price (numeric). "
            f"Return JSON: 'app', 'medicine', 'price', 'details'. Strict JSON."
        )

        k = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        prov = "GoogleGenAI" if self.provider == "gemini" else self.provider

        llm = load_llm(provider_name=prov, model=self.model, api_key=k)
        tool_set = await AdbTools.create()

        agent = DroidAgent(
            goal=goal,
            llm=llm,
            tools=tool_set,
            vision=True,
            reasoning=False
        )

        out_struct = {"app": app_name, "medicine": medicine, "status": "failed", "data": {}, "numeric_price": float('inf')}

        try:
            print(f"[PharmaAgent] 🧠 Running Agent on {app_name} for {medicine}...")
            res_obj = await agent.run()
            
            if res_obj:
                txt = str(getattr(res_obj, 'reason', getattr(res_obj, 'message', res_obj))).strip()

                if "<request_accomplished" in txt:
                    chunks = txt.split(">")
                    if len(chunks) > 1:
                        txt = chunks[1].split("</request_accomplished>")[0].strip()

                if "```" in txt:
                    seg = txt.split("```")
                    txt = seg[1] if len(seg) > 1 else txt
                    if txt.startswith("json"):
                        txt = txt[4:].strip()
                
                txt = txt.strip()
                
                if txt.startswith("{"):
                    try:
                        d = json.loads(txt)
                        out_struct["data"] = d
                        out_struct["status"] = "success"
                        out_struct["numeric_price"] = self._parse_price(d.get("price"))
                    except json.JSONDecodeError:
                        pass
            
            return out_struct

        except Exception as e:
            return out_struct

    async def compare_prices(self, meds_input, role, apps_filter=None):
        default_apps = ["Apollo 24|7", "Tata 1mg"]
        
        target_apps = default_apps
        if apps_filter:
            target_apps = [
                found for requested in apps_filter 
                if (found := next((a for a in default_apps if requested.lower() in a.lower()), None))
            ] or default_apps

        med_list = []
        if isinstance(meds_input, list):
             med_list = [{"name": m if isinstance(m, str) else m.get("name"), "qty": 1 if isinstance(m, str) else m.get("qty", 1)} for m in meds_input]
        else:
            for item in meds_input.split(','):
                parts = item.strip().split(':')
                med_list.append({"name": parts[0].strip(), "qty": int(parts[1].strip()) if len(parts) > 1 else 1})

        print(f"\n[PharmaAgent] Processing List: {med_list}")
        
        basket_results = {}

        for app in target_apps:
            print(f"\n--- Checking {app} ---")
            
            total = 0.0
            items = []
            complete = True
            
            for m in med_list:
                r = await self.execute_task(app, m['name'], role)
                
                if r["status"] == "success":
                    p = r["numeric_price"]
                    q = m['qty']
                    sub = p * q
                    total += sub
                    items.append({
                        "name": m['name'], "unit_price": p, "qty": q, "line_total": sub,
                        "details": r['data'].get("details", "")
                    })
                    print(f"  > Found {m['name']} @ {p} x {q} = {sub}")
                else:
                    print(f"  > Failed to find {m['name']}")
                    complete = False
                    break 
                
                await asyncio.sleep(2)

            basket_results[app] = {"total_cost": total, "items": items} if complete else {"status": "incomplete"}
            await asyncio.sleep(3)

        print(f"\n--- Final Aggregated Basket Results ---")
        
        valid_baskets = []
        for app, res in basket_results.items():
            if res.get("status") != "incomplete":
                print(f"{app}: Total = ₹{res['total_cost']:.2f}")
                valid_baskets.append({"app": app, "total": res["total_cost"], "items": res["items"]})
            else:
                print(f"{app}: Incomplete Basket")

        if valid_baskets:
            best = min(valid_baskets, key=lambda x: x["total"])
            print(f"\n🏆 Best Basket Deal: {best['app']} - ₹{best['total']:.2f}")
        else:
            print("\n❌ Could not determine best basket option.")

async def main():
    p = argparse.ArgumentParser()
    p.add_argument("--meds", required=True)
    p.add_argument("--role", choices=['patient', 'pharmacist'], default='patient')
    p.add_argument("--apps")
    args = p.parse_args()

    filter_list = [a.strip() for a in args.apps.split(',')] if args.apps else None
    
    agent = PharmacyAgent(model="models/gemini-2.5-flash")
    await agent.compare_prices(args.meds, args.role, filter_list)

if __name__ == "__main__":
    asyncio.run(main())
