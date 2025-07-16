import datetime
import random
from typing import Optional, NamedTuple
from ortools.sat.python import cp_model

from coordination_agent.shared_libraries.types import MatcherResponse

TimeSlotDict = dict[str, str]  # {"start": "isoformat", "end": "isoformat"}
UserAvailabilityDict = dict[str, list[TimeSlotDict]]  # {user_id: [TimeSlotDict, ...]}
FetchAvailabilityResponse = dict[str, str | dict[str, list[dict[str, str]]]] # {"status": "success", "result": {"user_id": [{"start": "isoformat", "end": "isoformat"}, ...]}}
GetMeetingTimesResponse = dict[str, str | list[list[dict[str, str]]]] # {"status": "success", "result": [[{"start": "isoformat", "end": "isoformat"}, ...], ...]}


class TimeRange(NamedTuple):
    """
    Immutable class representing a time range with datetime objects.
    Used internally for calculations while avoiding repeated conversions.
    """
    start: datetime.datetime
    end: datetime.datetime

    @classmethod
    def from_slot_dict(cls, slot: TimeSlotDict) -> 'TimeRange':
        """Convert a string-based TimeSlotDict to a TimeRange with datetime objects."""
        return cls(
            start=datetime.datetime.fromisoformat(slot["start"]),
            end=datetime.datetime.fromisoformat(slot["end"])
        )
    
    def to_slot_dict(self) -> TimeSlotDict:
        """Convert a TimeRange back to a string-based TimeSlotDict."""
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat()
        }
    
    def duration_minutes(self) -> int:
        """Calculate the duration of the time range in minutes."""
        return int((self.end - self.start).total_seconds() / 60)


def _generate_availability(
    num_slots: Optional[int] = None, 
) -> list[TimeSlotDict]:
    """
    Generate random time availability slots. Internal helper function.
    """
    date = datetime.datetime.now().date()
    raw_slots = []  # Store as datetime objects initially
    
    start_hour, end_hour = 9, 17
    
    possible_slots = []
    for hour in range(start_hour, end_hour):
        for minute in [0, 30]:
            start_time = datetime.datetime.combine(date, datetime.time(hour, minute))
            possible_slots.append(start_time)

    random.shuffle(possible_slots)
    selected_starts = sorted(possible_slots[:num_slots])
    
    for start_time in selected_starts:
        # Duration between 30 and 120 minutes
        duration = random.choice([30, 60, 90, 120])
        end_time = start_time + datetime.timedelta(minutes=duration)
        
        # Make sure end time doesn't exceed business hours
        day_end = datetime.datetime.combine(date, datetime.time(end_hour, 0))
        if end_time > day_end:
            end_time = day_end
        
        if start_time < end_time:  # Only add valid slots
            raw_slots.append((start_time, end_time))
    
    # Merge overlapping or adjacent slots
    if not raw_slots:
        return []

    raw_slots.sort(key=lambda x: x[0])
    
    merged_slots = []
    current_start, current_end = raw_slots[0]
    
    for start_time, end_time in raw_slots[1:]:
        # Check if current slot overlaps or is adjacent to the previous one
        if start_time <= current_end:  # Overlapping or adjacent
            # Extend the current slot to include this one
            current_end = max(current_end, end_time)
        else:
            # No overlap, add the previous merged slot and start a new one
            merged_slots.append({
                "start": current_start.isoformat(),
                "end": current_end.isoformat()
            })
            current_start, current_end = start_time, end_time
    
    # Add the last merged slot
    merged_slots.append({
        "start": current_start.isoformat(),
        "end": current_end.isoformat()
    })
    
    return merged_slots


def _generate_availabilities(
    user_ids: list[str],
    num_slots_per_user: Optional[int] = None,
) -> UserAvailabilityDict:
    """
    Generate random availability slots for a list of users. Internal wrapper function.
    """
    availabilities = {}
    
    for user_id in user_ids:
        availability = _generate_availability(num_slots_per_user)
        availabilities[user_id] = availability

    return availabilities


def fetch_time_availabilities(
    user_ids: list[str],
) -> dict[str, str | dict[str, list[dict[str, str]]]]:
    """
    Fetch time availability data for the given user IDs.
    
    Args:
        user_ids: list of user IDs to fetch availability for.
    
    Returns:
      dict[str, str | dict[str, list[dict[str, str]]]]]: A dictionary with the key `status` and
      `availabilities` where:
      - `status`: string indicating the status of the request. Possible values are:
        `success` and `error`.
      - `result`: A dictionary object representing availability slots for the users where
        the keys are user IDs and the values are lists of dictionaries objects representing
        availability slots, which is a dictionary containing `start` and `end` keys with
        datetime values in ISO8601 string format.

    Example success:
        >>> fetch_time_availabilities(user_ids=['123', '456'])
        {
            "status": "success",
            "result": {
                "123": [
                    {"start": "2023-10-01T09:00:00", "end": "2023-10-01T10:30:00"},
                    {"start": "2023-10-01T04:00:00", "end": "2023-10-01T04:30:00"}
                ],
                "456": [
                    {"start": "2023-10-01T09:00:00", "end": "2023-10-01T10:30:00"},
                    {"start": "2023-10-01T04:00:00", "end": "2023-10-01T04:30:00"}
                ],
            }
        }
    Example error:
        >>> fetch_time_availabilities(user_ids=['123', '456'])
        {
            "status": "error",
            "result": "Error fetching availability data"
        }
    """
    # This is a mock function and can be replaced with an API call
    num_slots = random.randint(3, 8)

    availabilities = _generate_availabilities(
        user_ids=user_ids,
        num_slots_per_user=num_slots,
    )   
    
    return {
        "status": "success",
        "result": availabilities,
    }


def _find_overlapping_times(
    users_availability: UserAvailabilityDict,
    min_duration_minutes: int = 30,
    start_time: Optional[datetime.datetime] = None,
    end_time: Optional[datetime.datetime] = None,
    block_time_minutes: int = 30
) -> list[TimeSlotDict]:
    """
    Find overlapping availability times between multiple users using Google OR-Tools.
    Time slots are aligned to specified minute blocks.
    
    Args:
        users_availability: Dictionary mapping user IDs to lists of TimeSlot objects
        min_duration_minutes: Minimum duration of overlap in minutes
        start_time: Optional start time boundary for the search
        end_time: Optional end time boundary for the search
        block_time_minutes: Size of time blocks in minutes (default: 30)
        
    Returns:
        List of TimeSlot objects representing times when all users are available
    """   
    # Ensure block_time_minutes is at least 15 minutes
    block_time_minutes = max(15, block_time_minutes)
    
    # Ensure min_duration is a multiple of block_time_minutes
    min_duration_minutes = max(block_time_minutes, 
                              ((min_duration_minutes + block_time_minutes - 1) // block_time_minutes) * block_time_minutes)
    
    # Collect all unique time points from all users
    all_time_points = set()

    # Convert time slots to TimeRange objects once
    user_time_ranges = {}
    for user_id, time_slots in users_availability.items():
        user_time_ranges[user_id] = [TimeRange.from_slot_dict(slot) for slot in time_slots]
        
        for time_range in user_time_ranges[user_id]:
            # Round start time down to nearest block_time_minutes mark if needed
            start_minutes = (time_range.start.minute // block_time_minutes) * block_time_minutes
            aligned_start = time_range.start.replace(minute=start_minutes, second=0, microsecond=0)
            
            # Round end time up to nearest block_time_minutes mark if needed
            end_minutes = ((time_range.end.minute + block_time_minutes - 1) // block_time_minutes) * block_time_minutes
            if end_minutes >= 60:  # Handle case where we round up to next hour
                hours_to_add = end_minutes // 60
                remaining_minutes = end_minutes % 60
                aligned_end = time_range.end.replace(minute=remaining_minutes, second=0, microsecond=0) + datetime.timedelta(hours=hours_to_add)
            else:
                aligned_end = time_range.end.replace(minute=end_minutes, second=0, microsecond=0)
                
            all_time_points.add(aligned_start)
            all_time_points.add(aligned_end)
    
    # Add boundaries if provided
    if start_time:
        # Round start time to nearest block_time_minutes mark
        start_minutes = (start_time.minute // block_time_minutes) * block_time_minutes
        aligned_start = start_time.replace(minute=start_minutes, second=0, microsecond=0)
        all_time_points.add(aligned_start)
        
    if end_time:
        # Round end time to nearest block_time_minutes mark
        end_minutes = ((end_time.minute + block_time_minutes - 1) // block_time_minutes) * block_time_minutes
        if end_minutes >= 60:
            hours_to_add = end_minutes // 60
            remaining_minutes = end_minutes % 60
            aligned_end = end_time.replace(minute=remaining_minutes, second=0, microsecond=0) + datetime.timedelta(hours=hours_to_add)
        else:
            aligned_end = end_time.replace(minute=end_minutes, second=0, microsecond=0)
        all_time_points.add(aligned_end)
    
    # Sort time points
    sorted_time_points = sorted(list(all_time_points))

    # Initialize the CP-SAT model
    model = cp_model.CpModel()
    
    # Create variables for each potential time interval
    intervals = []
    for i in range(len(sorted_time_points) - 1):
        t_start = sorted_time_points[i]
        t_end = sorted_time_points[i+1]
        
        # Check if interval is a multiple of block_time_minutes
        interval_duration = (t_end - t_start).total_seconds() / 60
        if interval_duration % block_time_minutes != 0:
            continue
            
        # Skip intervals that are too short
        if interval_duration < min_duration_minutes:
            continue
            
        # Skip intervals outside boundaries
        if (start_time and t_end <= start_time) or (end_time and t_start >= end_time):
            continue
        
        # Create a boolean variable for this interval
        is_available = model.NewBoolVar(f'interval_{i}_available')
        
        for user_id, time_ranges in user_time_ranges.items():
            user_available = False
            
            for slot_range in time_ranges:
                # If the interval is completely contained within the slot
                if t_start >= slot_range.start and t_end <= slot_range.end:
                    user_available = True
                    break
            
            # If user is not available in this interval, set is_available to False
            if not user_available:
                model.Add(is_available == 0)
                break
        
        intervals.append((is_available, t_start, t_end))
    
    # Add objective: maximize total available time
    model.Maximize(
        sum(is_available * ((t_end - t_start).total_seconds() / 60) 
            for is_available, t_start, t_end in intervals)
    )
    
    # Solve the model
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    
    # Extract solution
    overlapping_slots = []
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        current_slot_start = None
        current_slot_end = None
        
        for is_available, t_start, t_end in intervals:
            if solver.Value(is_available) == 1:
                if current_slot_start is None:
                    # Start a new slot
                    current_slot_start = t_start
                    current_slot_end = t_end
                elif t_start == current_slot_end:
                    # Extend current slot
                    current_slot_end = t_end
                else:
                    # End current slot and start new one
                    overlapping_slots.append(TimeRange(start=current_slot_start, end=current_slot_end))
                    current_slot_start = t_start
                    current_slot_end = t_end
        
        # Add the last slot if it exists
        if current_slot_start is not None:
            overlapping_slots.append(TimeRange(start=current_slot_start, end=current_slot_end))
    
    # Merge adjacent slots
    merged_slots: list[TimeRange] = []
    if overlapping_slots:
        current = overlapping_slots[0]
        for next_slot in overlapping_slots[1:]:
            if current.end == next_slot.start:
                # Merge
                current = TimeRange(start=current.start, end=next_slot.end)
            else:
                merged_slots.append(current)
                current = next_slot
        merged_slots.append(current)
    
    # Filter out slots that are too short and convert back to TimeSlotDict format
    result = [slot.to_slot_dict() for slot in merged_slots 
              if slot.duration_minutes() >= min_duration_minutes]
    
    return result


def _split_into_time_blocks(
        time_slots: list[TimeSlotDict],
        block_time_minutes: int = 30,
) -> list[TimeSlotDict]:
    """
    Split time slots into chunks of specified minutes. Internal helper function.
    """
    chunks = []
    
    for time_slot in time_slots:
        # Convert to TimeRange class for calculations
        slot_range = TimeRange.from_slot_dict(time_slot)
        current_time = slot_range.start
        
        while current_time + datetime.timedelta(minutes=block_time_minutes) <= slot_range.end:
            chunk_end = current_time + datetime.timedelta(minutes=block_time_minutes)
            chunks.append(TimeRange(start=current_time, end=chunk_end).to_slot_dict())
            current_time = chunk_end

    return chunks


def get_meet_times(
    user_ids: list[list[str]],
    user_availability: UserAvailabilityDict,
) -> GetMeetingTimesResponse:
    """
    Fetch available meeting times for groups of users. This function already calculates overlapping time slots
    based on the provided user ID groups.

    Args:
        user_ids (list[list[str]]): A list of user groups, where each group is a list of user ID strings.
            - Format: [["user1", "user2"], ["user3", "user4"], ...]
            - Each inner list represents users who need to meet together
            - User IDs should be strings (e.g., "123", "456")
        user_availability (dict[str, list[dict[str, str]]]): A dictionary mapping user IDs to lists of objects
            representing availability slots for those users.
            - Format: {"user1": [{"start": "ISO8601_datetime", "end": "ISO8601_datetime"}, ...], "user2": [{"start": "ISO8601_datetime", "end": "ISO8601_datetime"}]}

    Returns:
        dict: Response dictionary containing:
            - "status" (str): Either "success" or "error"
            - "result" (list[list[dict]]): When status is "success", contains availability data:
                * Outer list: One entry per user group (matches user_ids order)
                * Inner list: Available time slots for that group
                * Each slot dict has: {"start": "ISO8601_datetime", "end": "ISO8601_datetime"}

    Examples:
        Single group with overlapping availability:
        >>> get_meet_times(
        ...     user_ids=[["123", "456"]],
        ...     user_availability={
        ...         "123": [
        ...             {"start": "2023-10-01T09:00:00", "end": "2023-10-01T12:00:00"},
        ...             {"start": "2023-10-01T14:00:00", "end": "2023-10-01T17:00:00"}
        ...         ],
        ...         "456": [
        ...             {"start": "2023-10-01T10:00:00", "end": "2023-10-01T11:30:00"},
        ...             {"start": "2023-10-01T15:00:00", "end": "2023-10-01T16:00:00"}
        ...         ]
        ...     }
        ... )
        {
            "status": "success",
            "result": [
                [
                    {"start": "2023-10-01T10:00:00", "end": "2023-10-01T11:30:00"},  # Overlap 1
                    {"start": "2023-10-01T15:00:00", "end": "2023-10-01T16:00:00"}   # Overlap 2
                ]
            ]
        }
        
        Multiple groups with different availability:
        >>> get_meet_times(
        ...     user_ids=[["123", "456"], ["789", "654"]],
        ...     user_availability={
        ...         "123": [{"start": "2023-10-01T09:00:00", "end": "2023-10-01T12:00:00"}],
        ...         "456": [{"start": "2023-10-01T10:00:00", "end": "2023-10-01T11:00:00"}],
        ...         "789": [{"start": "2023-10-01T14:00:00", "end": "2023-10-01T16:00:00"}],
        ...         "654": [{"start": "2023-10-01T15:00:00", "end": "2023-10-01T17:00:00"}]
        ...     }
        ... )
        {
            "status": "success",
            "result": [
                [{"start": "2023-10-01T10:00:00", "end": "2023-10-01T11:00:00"}],  # Group 1 overlap
                [{"start": "2023-10-01T15:00:00", "end": "2023-10-01T16:00:00"}]   # Group 2 overlap
            ]
        }
        
        No overlapping availability:
        >>> get_meet_times(
        ...     user_ids=[["123", "456"]],
        ...     user_availability={
        ...         "123": [{"start": "2023-10-01T09:00:00", "end": "2023-10-01T11:00:00"}],
        ...         "456": [{"start": "2023-10-01T14:00:00", "end": "2023-10-01T16:00:00"}]
        ...     }
        ... )
        {
            "status": "success",
            "result": [
                []  # No overlapping time slots
            ]
        }
        
        Missing user in availability data:
        >>> get_meet_times(
        ...     user_ids=[["123", "456"]],
        ...     user_availability={
        ...         "123": [{"start": "2023-10-01T09:00:00", "end": "2023-10-01T11:00:00"}]
        ...         # "456" is missing
        ...     }
        ... )
        {
            "status": "error",
            "result": []
        }

    Usage Notes:
        - Always pass user_ids as a list of lists, even for a single group: [["user1", "user2"]]
        - User IDs must be strings, not integers
        - All user IDs in user_ids must have corresponding entries in user_availability
        - The function calculates overlapping time slots automatically - you provide individual availability
        - Empty result lists indicate no overlapping meeting times for that group
        - Times should be in ISO8601 format (YYYY-MM-DDTHH:MM:SS)
    """
    time_block_size = 30
    blocks = []
    
    for user_group in user_ids:
        # Filter availability for users in this group
        group_availability = {
            user_id: slots 
            for user_id, slots in user_availability.items() 
            if user_id in user_group
        }
        
        if not group_availability or len(group_availability) != len(user_group):
            blocks.append([])
            continue
            
        overlaps = _find_overlapping_times(
            users_availability=group_availability,
            min_duration_minutes=time_block_size,
            start_time=None,
            end_time=None,
            block_time_minutes=time_block_size
        )

        if overlaps:
            blocks.append(_split_into_time_blocks(overlaps, block_time_minutes=time_block_size))
        else:
            blocks.append([])

    return {
        "status": "success",
        "result": blocks,
    }


def extract_groups_and_users(matcher_response: MatcherResponse) -> dict[str, list[str] | list[list[str]]]:
    """
    Extract groups and users from a MatcherResponse for scheduling purposes.
    
    Args:
        matcher_response: MatcherResponse object containing matched groups
        
    Returns:
        dict: Dictionary containing:
            - "status": "success" if operation was successful, or "error" if an error occurred
            - "result": Dictionary containing extracted data when status is "success". Empty dictionary when status is "error".
            
    Example:
        >>> response = MatcherResponse(matched_groups={
        ...     "group1": UserGroup(id="group1", user_ids=["user1", "user2"]),
        ...     "group2": UserGroup(id="group2", user_ids=["user3", "user4"])
        ... })
        >>> extract_groups_and_users(response)
        {
            "status": "success",
            "result": {
                "groups": ["group1", "group2"],
                "users": ["user1", "user2", "user3", "user4"],
                "user_groups": [["user1", "user2"], ["user3", "user4"]]
            }
        }
        
        >>> extract_groups_and_users(None)
        {
            "status": "error",
            "result": {}
        }
    """
    try:
        if not isinstance(matcher_response, MatcherResponse):
            return {
                "status": "error",
                "result": {}
            }
            
        groups = list(matcher_response.matched_groups.keys())
        
        all_users = set()
        user_groups = []
        
        for group in matcher_response.matched_groups.values():
            if not hasattr(group, 'user_ids'):
                return {
                    "status": "error",
                    "result": {}
                }
            user_groups.append(group.user_ids)
            all_users.update(group.user_ids)
        
        result = {
            "groups": groups,
            "users": list(all_users),
            "user_groups": user_groups
        }
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        return {
            "status": "error",
            "result": {}
        }
