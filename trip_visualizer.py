from schemas import FullTripPlan

class TripVisualizer:
    @staticmethod
    def generate_mermaid(trip_plan: FullTripPlan) -> str:
        graph = ["graph TD"]
        
        graph.append(f"    Start((Home)) -->|Pick up| Cab1{{{{Cab: {trip_plan.arrival_cab.provider} {trip_plan.arrival_cab.pickup_time.strftime('%H:%M')}}}}}")
        
        def sanitize(text):
            if not text: return "Unknown"
            import re
            valid = re.sub(r'[^a-zA-Z0-9 :.-]', '', str(text))
            return valid.strip()

        flight_label = sanitize(f"Flight: {trip_plan.flight.airline} - {trip_plan.flight.flight_number}")
        flight_node = f'Flight["{flight_label}"]'
        
        cab_label = sanitize(f"Cab: {trip_plan.arrival_cab.provider} at {trip_plan.arrival_cab.pickup_time.strftime('%H:%M')}")
        cab_node = f'CabArr["{cab_label}"]'
        
        hotel_label = sanitize(f"Hotel: {trip_plan.hotel.name}")
        hotel_node = f'Hotel["{hotel_label}"]'
        
        graph.append(f'    Start((Home)) -->|Fly| {flight_node}')
        
        arr_time = trip_plan.flight.arrival_time.strftime("%H:%M")
        graph.append(f'    {flight_node} -->|Arrive {arr_time}| {cab_node}')
        graph.append(f'    {cab_node} -->|To Hotel| {hotel_node}')
        
        last_node = "Hotel"
        
        for day in trip_plan.daily_schedule:
            for i, activity in enumerate(day.activities):
                act_id = f"Day{day.day_number}Act{i}"
                label = sanitize(f"{activity.time}: {activity.description}")
                if len(label) > 40: label = label[:37] + "..."
                
                act_node = f'{act_id}["{label}"]'
                
                graph.append(f"    {last_node} -->|Next| {act_node}")
                last_node = act_id
        
        graph.append(f"    {last_node} --> End((Sleep))")
        
        final_code = "\n".join(graph)
        print(final_code)
        
        return final_code
