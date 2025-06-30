
def get_task_stats(user_id, subordinates,tasks):

    stats = {
        "own_task": 0,
        "subordinate_task": 0,
        "total_task": 0
       
    }

    for task in tasks:
        if not task.assigned_to_employee:
            continue
        if task.status.lower()== 'completed':
            stats["total_task"]+=1      
            if task.assigned_to_employee.id == user_id:
                stats["own_task"]+=1
            elif task.assigned_to_employee.id in subordinates:
                stats["subordinate_task"]+=1

    return stats
