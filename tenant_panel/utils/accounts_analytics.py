def get_accounts_stats(user_id, subordinates,accounts):

    stats = {
        "own_account": 0,
        "subordinate_account": 0,
        "total_account": 0
       
    }

    for account in accounts:
        if not account.assigned_to:
            continue
        
        if account.assigned_to.id == user_id:
            stats["own_account"]+=1
        elif account.assigned_to.id in subordinates:
            stats["subordinate_account"]+=1

    return stats