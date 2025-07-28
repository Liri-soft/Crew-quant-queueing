# Call Volume
CALL_VOLUME = {
    "Monday": [40, 33, 24, 20, 19, 18, 23, 23, 25, 21, 18, 27, 36, 50, 68, 107, 178, 233, 214, 250, 323, 311, 279, 264],
    "Tuesday": [210, 151, 130, 106, 76, 69, 81, 91, 98, 85, 91, 112, 127, 132, 151, 193, 223, 266, 261, 285, 345, 331, 333, 312],
    "Wednesday": [218, 191, 185, 129, 106, 100, 98, 110, 101, 90, 95, 111, 130, 151, 163, 185, 251, 307, 272, 309, 367,333, 342, 315],
    "Thursday": [224, 179, 148, 116, 88, 79, 92, 108, 114, 92, 99, 121, 132,159, 175, 197, 269, 296, 282,304, 368, 356, 323, 312],
    "Friday": [241, 182, 164, 126, 94, 91, 101, 120, 122, 103, 104, 124, 167, 160, 176, 336, 277, 303, 326, 293, 355, 341, 301, 296],
    "Saturday": [237, 170, 141, 122, 97, 87, 149, 116, 115, 104, 97, 121, 142,151, 159,204, 238, 261, 252, 252, 302, 283, 256, 239],
    "Sunday": [184, 151, 125, 101, 90, 81, 104, 111, 108, 95, 92, 105, 103, 104, 99, 99, 95, 100, 90, 79, 89, 81, 60, 53]
}
# Shift structure parameters
SHIFT_HOURS = 8          # Length of each shift (4, 6, 8, or 12)
AGENT_EFFICIENCY = 90  # Agent efficiency (e.g., 100% of time is productive)
# Call handling
AVG_HANDLING_TIME = 6.3   # Average handling time in minutes
AVG_PATIENCE = 180               # Average caller patience in seconds before abandonment
# Service level goals
TARGET_SLA = 20          # Target answer time in seconds (e.g., 20 seconds)
DESIRED_SLA = 95         # Target service level percentage (e.g., 95%)
# Call complexity distribution
CALL_COMPLEXITY_DISTRIBUTION = {
    # [normal, semicomplex, complex]
    "probabilities": [50, 30, 20], # addition all the probabilities should be 100% 
    "complexity_factors": {
        "semicomplex": 1.2,  # 20% longer handling time
        "complex": 1.8,      # 80% longer handling time
    }
}
# After call work time range (seconds)
ACW_MIN = 20
ACW_MAX = 30
# Break scheduling parameters
LUNCH_BREAK_TIME = 45  # Break duration in seconds (45 minutes)
# Maximum percentage of agents on break at once
MAX_PERCENTAGE_AGENTS_ON_BREAK = 30
