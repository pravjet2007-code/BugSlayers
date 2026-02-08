from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
from datetime import datetime

from agents.transit_agent import TransitManager
from agents.stay_agent import StayManager
from trip_visualizer import TripVisualizer
from schemas import FullTripPlan, FlightDetails, CabDetails, HotelDetails, ItineraryDay

app = FastAPI(title="Voyager-1 Travel Planner")

class TripRequest(BaseModel):
    source: str
    destination: str
    date: str
    user_interests: str

@app.post("/plan_trip", response_model=FullTripPlan)
async def plan_trip(request: TripRequest):
    print(f"🚀 Received Trip Request: {request}")
    
    transit_agent = TransitManager()
    stay_agent = StayManager()
    
    try:
        flight = await transit_agent.find_best_flight(request.source, request.destination, request.date)
        if not flight:
             raise HTTPException(status_code=500, detail="Could not find flight")
        
        cab = await transit_agent.book_cab(request.destination, flight.arrival_time)
        
        hotel = await stay_agent.find_hotel(request.destination, request.date)
        
        itinerary = await stay_agent.generate_itinerary(hotel.name, request.user_interests)
        
        full_plan = FullTripPlan(
            flight=flight,
            arrival_cab=cab,
            hotel=hotel,
            daily_schedule=itinerary
        )
        
        mermaid_code = TripVisualizer.generate_mermaid(full_plan)
        full_plan.flowchart_code = mermaid_code
        
        return full_plan

    except Exception as e:
        print(f"❌ Error Planning Trip: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
