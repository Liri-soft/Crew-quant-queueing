import simpy
import numpy as np
import random
from erlang_staffing import arrival_rate_urgent, URGENT_TASK_WORK_MINUTES, DAYS_OF_WEEK, HOURS_PER_DAY

# Convert minutes to seconds for simulation
AHT = URGENT_TASK_WORK_MINUTES * 60  # Average handling time in seconds
SIM_DURATION = 3600  # seconds (1 hour)
TARGET_SLA = 20  # Target answer time in seconds for service level calculation
AVG_PATIENCE = 120  # Average caller patience in seconds (2 minutes)


def run_simulation(num_agents, arrival_rate_per_hour, service_time_seconds=AHT, 
                   avg_patience_seconds=AVG_PATIENCE):
    
    if arrival_rate_per_hour == 0:
        return {
            "calls_arrived": 0,
            "calls_handled": 0,
            "calls_abandoned": 0,
            "calls_expected": 0,
            "avg_wait": 0,
            "max_wait": 0,
            "service_level": 100,
            "wait_times": [],
        }

    # Setup simulation
    env = simpy.Environment()
    agents = simpy.Resource(env, capacity=num_agents)
    
    wait_times = []
    calls_handled = 0
    calls_arrived = 0
    calls_abandoned = 0

    # Number of calls to generate
    NUM_CALLS = int(arrival_rate_per_hour)

    def call_generator(env, agents):
        nonlocal calls_arrived
        
        arrival_times = np.sort(np.random.uniform(0, SIM_DURATION, NUM_CALLS))
        last_time = 0
        for i, scheduled_time in enumerate(arrival_times):
            yield env.timeout(scheduled_time - last_time)
            calls_arrived += 1
            env.process(handle_call(env, agents))
            last_time = scheduled_time 

    def handle_call(env, agents):
        """Handle an incoming call with potential abandonment"""
        nonlocal calls_handled, calls_abandoned
        arrival_time = env.now
        
        # Generate patience time for this caller (exponential distribution)
        variable_service_time = np.random.exponential(service_time_seconds)
        # print(f"service times: {variable_service_time:.2f} seconds")
        patience = np.random.exponential(avg_patience_seconds)
        # print(f"patience: {patience:.2f} seconds")

        # Request an agent but might abandon if wait is too long
        with agents.request() as req:
            # Wait for either getting an agent or running out of patience
            results = yield env.timeout(patience) | req
            wait_time = env.now - arrival_time

            # Check if customer abandoned (timeout event occurred)
            if req not in results:
                calls_abandoned += 1
                return
            
            # Customer was served
            wait_times.append(wait_time)
            calls_handled += 1
            
            # Simulate service time
            yield env.timeout(variable_service_time)

    # Start the call generation process
    env.process(call_generator(env, agents))

    # Run the simulation for one hour
    env.run(until=SIM_DURATION)

    # Analyze Results
    if len(wait_times) > 0:
        wait_array = np.array(wait_times)
        avg_wait = np.mean(wait_array)
        max_wait = np.max(wait_array)
        # Service level: percentage of calls answered within target time
        service_level = np.mean(wait_array <= TARGET_SLA) * 100
    else:
        avg_wait = 0
        max_wait = 0
        service_level = 100
        

    return {
        "calls_arrived": calls_arrived,
        "calls_handled": calls_handled,
        "calls_abandoned": calls_abandoned,
        "calls_expected": arrival_rate_per_hour,
        "avg_wait": avg_wait,
        "max_wait": max_wait,
        "service_level": service_level,
        "wait_times": wait_times,
    }


def simulate_staffing_plan(staffing_needs):
    
    all_results = []

    for day in DAYS_OF_WEEK:
        day_results = []
        print(f"\nSimulating {day}:")

        for hour in range(HOURS_PER_DAY):
            num_agents = staffing_needs[day][hour]
            arrival_rate = arrival_rate_urgent[day][hour]

            # Run the simulation
            result = run_simulation(num_agents, arrival_rate)
            simulation_result = {
                "day": day,
                "hour": hour,
                "calls_expected": arrival_rate,
                "calls_arrived": result["calls_arrived"],
                "calls_handled": result["calls_handled"],
                "calls_abandoned": result["calls_abandoned"],
                "agents": num_agents,
                "avg_wait": result["avg_wait"],
                "max_wait": result["max_wait"],
                "service_level": result["service_level"],
                "wait_times": result["wait_times"]
            }

            day_results.append(simulation_result)

            # Print progress with abandonment info
            print(f"Hour {hour:2d}: {result['calls_arrived']} calls arrived, "
                  f"{result['calls_handled']:3.0f} handled, "
                  f"{result['calls_abandoned']:3.0f} abandoned/Not Answered, "
                  f"{result['avg_wait']:5.1f}s avg wait, "
                  f"{result['service_level']:5.1f}% SL with {num_agents} agents")

        all_results.extend(day_results)

        # Calculate day summary
        day_calls_handled = sum(r["calls_handled"] for r in day_results)
        day_calls_abandoned = sum(r["calls_abandoned"] for r in day_results)
        day_agents = sum(r["agents"] for r in day_results)
        day_sl = np.mean([r["service_level"] for r in day_results if r["calls_handled"] > 0])

        print(f"\n{day} Summary: {day_calls_handled:.0f} calls handled, "
              f"{day_calls_abandoned:.0f} abandoned/Not Answered, "
              f"{day_agents} agent hours, "
              f"{day_sl:.1f}% service level")

    # Calculate overall statistics
    total_calls_handled = sum(r["calls_handled"] for r in all_results)
    total_calls_abandoned = sum(r["calls_abandoned"] for r in all_results)
    total_agents = sum(r["agents"] for r in all_results)
    overall_sl = np.mean([r["service_level"] for r in all_results if r["calls_handled"] > 0])

    print("\nOverall Weekly Statistics:")
    print(f"Total calls handled: {total_calls_handled:.0f}")
    print(f"Total calls abandoned/Not Answered: {total_calls_abandoned:.0f}")
    print(f"Total agent hours: {total_agents}")
    print(f"Overall service level: {overall_sl:.1f}%")

    return all_results

