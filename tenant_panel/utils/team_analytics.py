from django.utils import timezone

def get_team_stats(team_id,tasks):


    stats = {
        "pending_task": 0,
        "completed_task": 0,
        "total_task": 0,
        "due_task":0
       
    }
    today = timezone.now().date()

    for task in tasks:
        if not task.assigned_to_team:
            continue
        
        stats["total_task"]+=1
        if task.status.lower()== 'completed':
            
            stats["completed_task"]+=1 
        else:     
            if task.duedate and task.duedate<today:
                stats["due_task"]+=1
            else:
                stats["pending_task"]+=1


    return stats