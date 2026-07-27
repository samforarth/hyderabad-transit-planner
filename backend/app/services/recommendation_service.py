"""
Service for scoring, ranking, and generating explanations for journeys.
Helps the user understand why a particular route is recommended.
"""

import logging
from app.utils.time_utils import time_to_minutes

logger = logging.getLogger(__name__)

def score_journey(journey: dict, walking_to_source: float, walking_from_dest: float) -> float:
    """
    Calculates a score for a journey (LOWER is better).
    Weights represent passenger perceived disutility:
    - Travel time is standard base (weight 1.0).
    - Transfer wait time is penalized heavily (weight 1.5) — waiting at a stop feels worse than riding.
    - Walking requires effort (200m ~ 1 point).
    - Transfers are penalized (each transfer feels like a 15 min penalty).
    """
    total_duration = journey.get("total_duration_mins", 0)
    
    # Calculate actual riding time vs waiting time
    # Riding time = sum of each leg's duration (departure to arrival)
    # Transfer wait = total duration - riding time
    legs = journey.get("legs", [])
    riding_time = 0
    for leg in legs:
        dep = time_to_minutes(leg["departure_time"])
        arr = time_to_minutes(leg["arrival_time"])
        riding_time += max(0, arr - dep)
    
    # Transfer wait is the gap between legs (total duration minus riding time)
    transfer_wait = max(0, total_duration - riding_time)
    
    walking_distance = walking_to_source + walking_from_dest
    transfers = journey.get("transfers", 0)
    
    score = (
        riding_time * 1.0 +       # Actual time on the bus
        transfer_wait * 1.5 +      # Waiting at stops feels 50% worse than riding
        walking_distance * 0.005 + # Walking effort
        transfers * 15             # Fixed penalty per transfer
    )
    
    return score

def generate_explanation(journey: dict, best_journey: dict, walking_to: float, walking_from: float) -> str:
    """
    Generates a human-readable explanation comparing this journey to the best one.
    """
    if journey == best_journey:
        walk_total = int(walking_to + walking_from)
        transfers = journey.get("transfers", 0)
        transfer_text = "direct (no transfers)" if transfers == 0 else f"{transfers} transfer(s)"
        
        # Add transfer wait info if applicable
        wait_mins = journey.get("transfer_wait_mins", 0)
        wait_text = f", ~{int(wait_mins)} min wait" if wait_mins > 0 else ""
        
        return f"Recommended because: reasonable travel time, {transfer_text}{wait_text}, walk only {walk_total}m"
        
    # It's an alternative
    time_diff = journey.get("total_duration_mins", 0) - best_journey.get("total_duration_mins", 0)
    time_text = f"{abs(time_diff)} minutes slower" if time_diff > 0 else f"{abs(time_diff)} minutes faster"
    
    transfers = journey.get("transfers", 0)
    best_transfers = best_journey.get("transfers", 0)
    
    transfer_text = ""
    if transfers < best_transfers:
        transfer_text = " but fewer transfers"
    elif transfers == 0:
        transfer_text = " but direct (no transfers)"
        
    return f"Alternative: {time_text}{transfer_text}"

def rank_journeys(journeys: list, source_walking: dict, dest_walking: dict) -> dict:
    """
    Ranks journeys by score and generates explanations.
    """
    if not journeys:
        return {"recommended": None, "alternatives": []}
        
    scored_journeys = []
    for j in journeys:
        # Get first leg board stop and last leg alight stop to look up walking distances
        first_leg = j["legs"][0]
        last_leg = j["legs"][-1]
        
        walk_to = source_walking.get(first_leg["board_stop_id"], 0.0)
        walk_from = dest_walking.get(last_leg["alight_stop_id"], 0.0)
        
        score = score_journey(j, walk_to, walk_from)
        scored_journeys.append({"journey": j, "score": score, "walk_to": walk_to, "walk_from": walk_from})
        
    # Sort by score ascending
    scored_journeys.sort(key=lambda x: x["score"])
    
    best_entry = scored_journeys[0]
    best_journey = best_entry["journey"]
    
    recommended = best_journey.copy()
    recommended["reason"] = generate_explanation(best_journey, best_journey, best_entry["walk_to"], best_entry["walk_from"])
    recommended["walking_to_source_meters"] = best_entry["walk_to"]
    recommended["walking_from_dest_meters"] = best_entry["walk_from"]
    
    alternatives = []
    for entry in scored_journeys[1:]:
        alt_journey = entry["journey"].copy()
        alt_journey["reason"] = generate_explanation(alt_journey, best_journey, entry["walk_to"], entry["walk_from"])
        alt_journey["walking_to_source_meters"] = entry["walk_to"]
        alt_journey["walking_from_dest_meters"] = entry["walk_from"]
        alternatives.append(alt_journey)
        
    return {
        "recommended": recommended,
        "alternatives": alternatives
    }
