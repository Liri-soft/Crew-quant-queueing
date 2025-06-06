import shift_optimizer
import erlang_staffing
import matplotlib.pyplot as plt
import numpy as np


def find_ideal_shift_pattern(staffing_needs):
    """
    Find the ideal shift pattern to use consistently across all days of the week
    
    Parameters:
    staffing_needs (dict): Dictionary with staffing needs for each day and hour
    
    Returns:
    dict: Information about the optimal pattern and its weekly resource requirements
    """
    print("\nAnalyzing patterns for consistent weekly scheduling...")
    all_patterns = shift_optimizer.generate_shift_patterns()
    weekly_pattern_stats = []
    
    # For each pattern, calculate total resources needed across all days
    for pattern in all_patterns:
        pattern_number = pattern['pattern_number']
        total_weekly_agents = 0
        total_weekly_hours = 0
        daily_stats = []
        
        # Evaluate this pattern for each day
        for day in erlang_staffing.DAYS_OF_WEEK:
            evaluated_pattern = shift_optimizer.evaluate_shift_pattern(
                pattern, staffing_needs[day])
            
            # Add to weekly totals
            total_weekly_agents += evaluated_pattern['total_agents']
            total_weekly_hours += evaluated_pattern['total_agent_hours']
            
            # Calculate utilization for this day
            total_staff_hours = sum(staffing_needs[day])
            utilization = (total_staff_hours / evaluated_pattern['total_agent_hours']) * 100 if evaluated_pattern['total_agent_hours'] > 0 else 0
            
            # Store daily data
            daily_stats.append({
                'day': day,
                'agents': evaluated_pattern['total_agents'],
                'hours': evaluated_pattern['total_agent_hours'],
                'utilization': round(utilization, 1),
                'shifts': evaluated_pattern['shifts']
            })
        
        # Store pattern summary
        weekly_pattern_stats.append({
            'pattern_number': pattern_number,
            'total_weekly_agents': total_weekly_agents,
            'total_weekly_hours': total_weekly_hours,
            'avg_utilization': round(sum(day['utilization'] for day in daily_stats) / len(daily_stats), 1),
            'daily_stats': daily_stats,
            'shift_times': [f"{shift['start_hour']:02d}:00-{shift['end_hour']:02d}:00" for shift in pattern['shifts']]
        })
    
    # Find the optimal pattern (minimizing total agent hours)
    optimal_pattern = min(weekly_pattern_stats, key=lambda p: p['total_weekly_hours'])
    
    return optimal_pattern


def display_ideal_shift_pattern(optimal_pattern):
    """Display the results of the ideal shift pattern analysis"""
    print("\n=== IDEAL WEEKLY SHIFT PATTERN ===")
    print(f"Pattern {optimal_pattern['pattern_number']} is optimal for consistent weekly scheduling:")
    print(f"Total weekly agents required: {optimal_pattern['total_weekly_agents']}")
    print(f"Total weekly agent hours: {optimal_pattern['total_weekly_hours']}")
    print(f"Average utilization: {optimal_pattern['avg_utilization']}%")
    print("\nShift times for this pattern:")
    
    for i, shift_time in enumerate(optimal_pattern['shift_times']):
        shift_names = ["First", "Second", "Third", "Fourth", "Fifth"]
        shift_type = shift_names[i] if i < len(shift_names) else f"Shift {i+1}"
        print(f"  {shift_type} Shift: {shift_time}")
    
    print("\nDaily breakdown with this pattern:")
    for day_stat in optimal_pattern['daily_stats']:
        print(f"\n{day_stat['day']}: {day_stat['agents']} agents, {day_stat['hours']} agent hours, {day_stat['utilization']}% utilization")
        for i, shift in enumerate(day_stat['shifts']):
            shift_names = ["First", "Second", "Third", "Fourth", "Fifth"]
            shift_type = shift_names[i] if i < len(shift_names) else f"Shift {i+1}"
            start_time = f"{shift['start_hour']:02d}:00"
            end_time = f"{shift['end_hour']:02d}:00"
            agents = shift['agents_needed']
            agent_hours = shift['agent_hours']
            print(f"  {shift_type} Shift ({start_time}-{end_time}): {agents} agents, {agent_hours} agent hours")


def visualize_pattern_comparison(weekly_pattern_stats):
    """Create a bar chart comparing the resource requirements of each pattern"""
    patterns = [p['pattern_number'] for p in weekly_pattern_stats]
    agent_hours = [p['total_weekly_hours'] for p in weekly_pattern_stats]
    
    plt.figure(figsize=(12, 6))
    bars = plt.bar(patterns, agent_hours, color='skyblue')
    
    # Highlight the optimal pattern
    optimal_idx = agent_hours.index(min(agent_hours))
    bars[optimal_idx].set_color('green')
    
    plt.xlabel('Pattern Number')
    plt.ylabel('Total Weekly Agent Hours')
    plt.title('Comparison of Weekly Resource Requirements by Pattern')
    plt.xticks(patterns)
    
    # Add value labels on top of each bar
    for i, bar in enumerate(bars):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                f'{agent_hours[i]}',
                ha='center', va='bottom')
    
    plt.savefig('pattern_comparison.png')
    plt.close()
    print("\nPattern comparison chart saved as 'pattern_comparison.png'")


if __name__ == "__main__":
    # This allows the script to be run directly
    print("Calculating staffing needs...")
    staffing_needs = erlang_staffing.calculate_hourly_staffing_needs()
    
    optimal_pattern = find_ideal_shift_pattern(staffing_needs)
    display_ideal_shift_pattern(optimal_pattern)
    
    # Visualize the comparison
    weekly_pattern_stats = []  # You would need to recalculate this
    visualize_pattern_comparison(weekly_pattern_stats)