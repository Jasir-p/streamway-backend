def get_meeting_stats(user_id, subordinates,meetings):

    stats = {
        "own_meeting": 0,
        "subordinate_meeting": 0,
        "total_meeting": 0
       
    }

    for meeting in meetings:
        if not meeting.host:
            continue
        if meeting.status.lower()== 'completed':
            stats["total_meeting"]+=1      
            if meeting.host.id == user_id:
                stats["own_meeting"]+=1
            elif meeting.host.id in subordinates:
                stats["subordinate_meeting"]+=1

    return stats
