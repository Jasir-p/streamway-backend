
def get_deal_stats(user_id, subordinates, deals):

    stats = {
        "own_deals": 0,
        "subordinate_deals": 0,
        "converted_deals": 0,
        "total_deals": 0,
        "total_deal_value": 0,
        'own_value':0,
        'subordinate_value':0,
    
    }

    for deal in deals:
        if not deal.owner:
            continue
        if deal.stage.lower()== 'closed_won':
            stats["total_deals"]+=1
            
            stats["total_deal_value"]+=deal.amount
            if deal.owner.id == user_id:
                stats["own_deals"]+=1
                stats["own_value"]+=deal.amount
            elif deal.owner.id in subordinates:
                stats["subordinate_deals"]+=1
                stats["subordinate_value"]+=deal.amount

    return stats
