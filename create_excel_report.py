import pandas as pd
import numpy as np 
import erlang_staffing
import shift_optimizer
import os


def create_excel_report(staffing_needs, ideal_pattern, simulation_results=None):    
    """
    Create a comprehensive Excel report with all staffing data and shift information

    Parameters:
    staffing_needs (dict): Dictionary with staffing needs for each day and hour
    shift_plan (dict): Dictionary with optimal shift pattern for each day
    """
    print("\nCreating Excel report...")

    # Create a new Excel writer
    excel_path = 'StaffingReport.xlsx'
    writer = pd.ExcelWriter(excel_path, engine='openpyxl')

    # Create a sheet for hourly staffing needs
    hours = list(range(erlang_staffing.HOURS_PER_DAY))
    staffing_df = pd.DataFrame(index=hours)

    for day in erlang_staffing.DAYS_OF_WEEK:
        staffing_df[day] = staffing_needs[day]

    # Add time labels for easier reading
    staffing_df.index = [f"{hour}:00" for hour in hours]
    staffing_df.index.name = "Hour"

    # Save to Excel sheet
    staffing_df.to_excel(writer, sheet_name='Hourly Staffing Needs')

    # Create a sheet for shift patterns
    all_patterns = shift_optimizer.generate_shift_patterns()
    pattern_data = []

    for pattern in all_patterns:
        pattern_info = {
            'Pattern Number': pattern['pattern_number']
        }

        # Add shift information
        for i, shift in enumerate(pattern['shifts']):
            shift_type = "First" if i == 0 else (
                "Second" if i == 1 else "Third")
            start_time = f"{shift['start_hour']:02d}:00"
            end_time = f"{shift['end_hour']:02d}:00"
            pattern_info[f'{shift_type} Shift Start'] = start_time
            pattern_info[f'{shift_type} Shift End'] = end_time
            pattern_info[f'{shift_type} Shift Hours'] = ','.join(
                str(h) for h in shift['hours'])

        pattern_data.append(pattern_info)

    patterns_df = pd.DataFrame(pattern_data)
    patterns_df.to_excel(writer, sheet_name='Shift Patterns', index=False)

    # Create a sheet for pattern evaluation by day
    for day in erlang_staffing.DAYS_OF_WEEK:
        day_data = []

        for pattern in all_patterns:
            evaluated_pattern = shift_optimizer.evaluate_shift_pattern(
                pattern, staffing_needs[day])

            # Calculate utilization using agent hours
            total_staff_hours = sum(staffing_needs[day])
            total_agent_hours = evaluated_pattern['total_agent_hours']
            utilization = (total_staff_hours / total_agent_hours) * \
                100 if total_agent_hours > 0 else 0

            pattern_info = {
                'Pattern Number': pattern['pattern_number'],
                'Total Agents': evaluated_pattern['total_agents'],
                'Agent Hours': evaluated_pattern['total_agent_hours'],
                'Utilization (%)': round(utilization, 1),
                # 'Is Optimal': 'Yes' if is_optimal else 'No'
            }

            # Add shift details
            for i, shift in enumerate(evaluated_pattern['shifts']):
                shift_names = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth"]
                shift_type = shift_names[i] if i < len(shift_names) else f"Shift {i+1}"
                start_time = f"{shift['start_hour']:02d}:00"
                end_time = f"{shift['end_hour']:02d}:00"
                agents = shift['agents_needed']
                agent_hours = shift['agent_hours']

                pattern_info[f'{shift_type} Shift Time'] = f"{start_time}-{end_time}"
                pattern_info[f'{shift_type} Shift Agents'] = agents
                pattern_info[f'{shift_type} Shift Hours'] = agent_hours

            day_data.append(pattern_info)

        # Create DataFrame and save to Excel
        day_df = pd.DataFrame(day_data)
        day_df = day_df.sort_values('Total Agents')  # Sort by total agents
        day_df.to_excel(writer, sheet_name=f'{day} Patterns', index=False)

        # Add a sheet for the ideal weekly shift pattern
    if ideal_pattern:
        # Create summary table for the ideal pattern
        ideal_summary = pd.DataFrame([{
            'Pattern Number': ideal_pattern['pattern_number'],
            'Total Weekly Agents': ideal_pattern['total_weekly_agents'],
            'Total Weekly Hours': ideal_pattern['total_weekly_hours'],
            'Average Utilization (%)': ideal_pattern['avg_utilization']
        }])
        
        # Create shift times table
        shift_times_data = []
        for i, shift_time in enumerate(ideal_pattern['shift_times']):
            shift_names = ["First", "Second", "Third", "Fourth", "Fifth"]
            shift_type = shift_names[i] if i < len(shift_names) else f"Shift {i+1}"
            shift_times_data.append({
                'Shift': shift_type,
                'Time': shift_time
            })
        shift_times_df = pd.DataFrame(shift_times_data)
        
        # Create daily breakdown table
        daily_data = []
        for day_stat in ideal_pattern['daily_stats']:
            day_info = {
                'Day': day_stat['day'],
                'Total Agents': day_stat['agents'],
                'Agent Hours': day_stat['hours'],
                'Utilization (%)': day_stat['utilization']
            }
            
            # Add shift details
            for i, shift in enumerate(day_stat['shifts']):
                shift_names = ["First", "Second", "Third", "Fourth", "Fifth"]
                shift_type = shift_names[i] if i < len(shift_names) else f"Shift {i+1}"
                agents = shift['agents_needed']
                agent_hours = shift['agent_hours']
                
                day_info[f'{shift_type} Shift Agents'] = agents
                day_info[f'{shift_type} Shift Hours'] = agent_hours
                
            daily_data.append(day_info)
            
        daily_df = pd.DataFrame(daily_data)
        
        # Write to Excel with appropriate spacing
        ideal_summary.to_excel(writer, sheet_name='Ideal Weekly Pattern', index=False)
        
        # Add shift times table a few rows below
        shift_times_df.to_excel(writer, sheet_name='Ideal Weekly Pattern', 
                              startrow=ideal_summary.shape[0] + 3, index=False)
        
        # Add daily breakdown table a few rows below that
        daily_df.to_excel(writer, sheet_name='Ideal Weekly Pattern', 
                        startrow=ideal_summary.shape[0] + shift_times_df.shape[0] + 6, index=False)
    
    # Add simulation results if available
    if simulation_results:
        add_simulation_results_to_excel(writer, simulation_results)

    # Save and close the Excel file
    writer.close()

    print(f"Excel report saved to {excel_path}")

def add_simulation_results_to_excel(writer, simulation_results):
    """
    Add simulation results to the Excel report with all shifts in one sheet
    
    Parameters:
    writer: Excel writer object
    simulation_results (dict): Results from shift simulation
    """
    # Collect all shifts in a single list
    all_shifts = []
    
    for day, day_results in simulation_results.items():
        for shift in day_results:
            shift_data = {
                'Day': day,
                'Shift Type': shift['shift_type'],
                'Start Time': shift['start_time'],
                'End Time': shift['end_time'],
                'Hours Covered': ','.join(str(h) for h in shift['hours']),
                'Agents': shift['agents'],
                'Expected Calls': shift['calls_expected'],
                'Actual Calls': shift['calls_arrived'],
                'Calls Handled': shift['calls_handled'],
                'Calls Abandoned': shift['calls_abandoned'],
                'Average Wait (sec)': round(shift['avg_wait'], 1),
                'Maximum Wait (sec)': round(shift['max_wait'], 1),
                'Service Level (%)': round(shift['service_level'], 1),
            }
            all_shifts.append(shift_data)
    
    # Create a single DataFrame with all shifts and save to Excel
    all_shifts_df = pd.DataFrame(all_shifts)
    all_shifts_df.to_excel(writer, sheet_name='All Shifts Simulation', index=False)
    
    # Create a simulation summary
    summary_data = []
    for day, day_results in simulation_results.items():
        day_calls = sum(r["calls_arrived"] for r in day_results)
        day_handled = sum(r["calls_handled"] for r in day_results)
        day_abandoned = sum(r["calls_abandoned"] for r in day_results)
        day_sl = np.mean([r["service_level"] for r in day_results if r["calls_handled"] > 0])
        total_agents = sum(r["agents"] for r in day_results)
        
        summary_data.append({
            'Day': day,
            'Total Calls': day_calls,
            'Calls Handled': day_handled,
            'Calls Abandoned': day_abandoned,
            'Service Level (%)': round(day_sl, 1),
            'Total Agents': total_agents
        })
    
    # Add weekly total
    all_day_calls = sum(d['Total Calls'] for d in summary_data)
    all_day_handled = sum(d['Calls Handled'] for d in summary_data)
    all_day_abandoned = sum(d['Calls Abandoned'] for d in summary_data)
    all_day_sl = np.mean([d['Service Level (%)'] for d in summary_data])
    
    summary_data.append({
        'Day': 'WEEKLY TOTAL',
        'Total Calls': all_day_calls,
        'Calls Handled': all_day_handled,
        'Calls Abandoned': all_day_abandoned,
        'Service Level (%)': round(all_day_sl, 1),
        'Total Agents': total_agents
    })

    summary_df = pd.DataFrame(summary_data)
    summary_df.to_excel(writer, sheet_name='Simulation Summary', index=False)


if __name__ == "__main__":
    print("To generate an Excel report, run main.py")
